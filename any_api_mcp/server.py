from fastmcp import FastMCP
from any_api_mcp.loader import load_config, parse_tools, create_tool
import os


def create_server(config_path: str = "config.yaml") -> FastMCP:
    config = load_config(config_path)
    server_name = config.get("server_name", "Dynamic MCP Server")
    
    mcp = FastMCP(server_name)
    
    tools = parse_tools(config)
    
    for i, tool_def in enumerate(tools):
        tool_func = create_tool(tool_def)
        properties = tool_def.input_schema.get("properties", {})
        
        if not properties:
            @mcp.tool(name=tool_def.name, description=tool_def.description)
            def make_no_params(_func=tool_func, _idx=i):
                async def inner():
                    return await _func()
                return inner
        else:
            param_names = list(properties.keys())
            args_str = ", ".join(param_names)
            code = f"async def tool_{i}({args_str}):\n"
            code += f"    return await _tool_func({args_str})\n"
            
            local_vars = {"_tool_func": tool_func}
            compiled = compile(code, "<generated>", "exec")
            exec(compiled, {}, local_vars)
            
            tool_fn = local_vars[f"tool_{i}"]
            tool_fn.__name__ = tool_def.name
            tool_fn.__doc__ = tool_def.description
            
            @mcp.tool(name=tool_def.name, description=tool_def.description)
            def make_with_params(_func=tool_fn, _idx=i):
                async def inner(**kwargs):
                    filtered = {k: v for k, v in kwargs.items() if k in _func.__code__.co_varnames}
                    return await _func(**filtered)
                return inner
    
    return mcp


def main():
    config_path = os.environ.get("CONFIG_PATH", "config.yaml")
    mcp = create_server(config_path)
    mcp.run()