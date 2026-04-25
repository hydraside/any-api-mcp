import argparse
import os


def main():
    parser = argparse.ArgumentParser(
        prog="any-api-mcp",
        description="Dynamic MCP server with YAML configuration"
    )
    parser.add_argument(
        "config",
        nargs="?",
        default=os.environ.get("CONFIG_PATH", "config.yaml"),
        help="Path to YAML config file"
    )
    parser.add_argument(
        "--transport",
        "-t",
        default="stdio",
        choices=["stdio", "sse"],
        help="Transport type (default: stdio)"
    )
    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=8000,
        help="Port for SSE transport (default: 8000)"
    )
    
    args = parser.parse_args()
    
    from any_api_mcp.server import create_server
    mcp = create_server(args.config)
    
    if args.transport == "sse":
        mcp.run(transport="sse", port=args.port)
    else:
        mcp.run()


if __name__ == "__main__":
    main()