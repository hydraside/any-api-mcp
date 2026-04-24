from fastmcp import FastMCP
from any_api_mcp.loader import load_config, parse_tools, create_tool
import os


def create_server(config_path: str = "config.yaml") -> FastMCP:
    config = load_config(config_path)
    server_name = config.get("server_name", "Dynamic MCP Server")
    
    mcp = FastMCP(server_name)
    
    tools = parse_tools(config)
    
    for tool_def in tools:
        tool_func = create_tool(tool_def)
        
        @mcp.tool(name=tool_def.name, description=tool_def.description)
        async def execute_tool(tool_func=tool_func, **kwargs):
            return await tool_func(**kwargs)
    
    return mcp


if __name__ == "__main__":
    config_path = os.environ.get("CONFIG_PATH", "config.yaml")
    mcp = create_server(config_path)
    mcp.run()