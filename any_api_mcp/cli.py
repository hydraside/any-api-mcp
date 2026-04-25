import argparse
import os
import logging
import sys


logger = logging.getLogger("any_api_mcp")


def setup_logging(level: str = "INFO"):
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    
    logger.setLevel(log_level)
    logger.handlers.clear()
    logger.addHandler(handler)
    
    return logger


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
        "-c", "--config",
        dest="config_path",
        help="Path to YAML config file (overrides positional argument)"
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
    parser.add_argument(
        "--log-level",
        "-l",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)"
    )
    parser.add_argument(
        "--log-file",
        dest="log_file",
        help="Log file path (optional)"
    )
    
    args = parser.parse_args()
    
    if args.log_file:
        file_handler = logging.FileHandler(args.log_file)
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        ))
        logging.getLogger("any_api_mcp").addHandler(file_handler)
    
    logger = setup_logging(args.log_level)
    
    config_path = args.config_path or args.config
    
    logger.info(f"Starting any-api-mcp with config: {config_path}")
    logger.info(f"Transport: {args.transport}" + (f", Port: {args.port}" if args.transport == "sse" else ""))
    
    from any_api_mcp.server import create_server
    
    try:
        mcp = create_server(config_path)
        logger.info(f"Server '{mcp.name}' created successfully")
        
        if args.transport == "sse":
            logger.info(f"Starting SSE server on port {args.port}")
            mcp.run(transport="sse", port=args.port)
        else:
            logger.info("Starting STDIO server")
            mcp.run()
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise


if __name__ == "__main__":
    main()