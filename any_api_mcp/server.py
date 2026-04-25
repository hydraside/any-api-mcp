from fastmcp import FastMCP
from any_api_mcp.loader import load_config, parse_tools, create_tool
import os
import types
import ast


def create_typed_tool_function(tool_def, tool_func):
    input_schema = tool_def.input_schema
    properties = input_schema.get("properties", {})
    
    param_names = list(properties.keys())
    
    code = f"async def {tool_def.name}({', '.join(param_names)}):\n"
    code += f"    return await _tool_func({', '.join(param_names)})\n"
    
    local_vars = {"_tool_func": tool_func}
    compiled = compile(code, "<generated>", "exec")
    exec(compiled, {}, local_vars)
    
    func = local_vars[tool_def.name]
    func.__name__ = tool_def.name
    func.__doc__ = tool_def.description
    
    return func


def create_server(config_path: str = "config.yaml") -> FastMCP:
    config = load_config(config_path)
    server_name = config.get("server_name", "Dynamic MCP Server")
    
    mcp = FastMCP(server_name)
    
    tools = parse_tools(config)
    
    for tool_def in tools:
        tool_func = create_tool(tool_def)
        
        if not tool_def.input_schema.get("properties"):
            async def simple_tool(_func=tool_func):
                return await _func()
            simple_tool.__name__ = tool_def.name
            simple_tool.__doc__ = tool_def.description
            tool_fn = simple_tool
        else:
            tool_fn = create_typed_tool_function(tool_def, tool_func)
        
        @mcp.tool(name=tool_def.name, description=tool_def.description)
        async def execute_tool(tool_func=tool_fn):
            return await tool_func()
    
    return mcp


def main():
    config_path = os.environ.get("CONFIG_PATH", "config.yaml")
    mcp = create_server(config_path)
    mcp.run()