import pytest
from any_api_mcp.loader import (
    load_config,
    parse_tools,
    parse_headers,
    ToolDefinition,
    HandlerType,
    AuthConfig,
)


class TestParseHeaders:
    def test_parse_dict_headers(self):
        headers = {"Authorization": "Bearer token", "X-Key": "value"}
        result = parse_headers(headers)
        assert result == {"Authorization": "Bearer token", "X-Key": "value"}

    def test_parse_list_headers(self):
        headers = [
            {"name": "Authorization", "value": "Bearer token"},
            {"name": "X-Custom", "value": "test"},
        ]
        result = parse_headers(headers)
        assert result == {"Authorization": "Bearer token", "X-Custom": "test"}

    def test_parse_string_headers(self):
        headers = ["Authorization: Bearer token", "X-Key: value"]
        result = parse_headers(headers)
        assert result == {"Authorization": "Bearer token", "X-Key": "value"}

    def test_parse_empty_headers(self):
        assert parse_headers(None) == {}
        assert parse_headers({}) == {}
        assert parse_headers([]) == {}


class TestAuthConfig:
    def test_auth_config_defaults(self):
        auth = AuthConfig()
        assert auth.type == "none"
        assert auth.header == "Authorization"
        assert auth.prefix == "Bearer"

    def test_auth_config_from_dict(self):
        data = {
            "type": "bearer",
            "token": "my-token",
        }
        auth = AuthConfig.from_dict(data)
        assert auth.type == "bearer"
        assert auth.get_headers("my-token") == {"Authorization": "Bearer my-token"}

    def test_api_key_auth(self):
        data = {"type": "api_key", "header": "X-API-Key", "token": "key123"}
        auth = AuthConfig.from_dict(data)
        assert auth.get_headers("key123") == {"X-API-Key": "key123"}

    def test_basic_auth(self):
        data = {"type": "basic", "username": "user", "password": "pass"}
        auth = AuthConfig.from_dict(data)
        headers = auth.get_headers()
        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Basic ")


class TestLoadConfig:
    def test_load_yaml_config(self):
        config = load_config("config.yaml")
        assert "tools" in config or "swagger" in config

    def test_parse_tools_from_yaml(self):
        config = {
            "tools": [
                {
                    "name": "test_tool",
                    "description": "A test tool",
                    "input_schema": {
                        "type": "object",
                        "properties": {"id": {"type": "integer"}},
                    },
                    "handler": {
                        "url": "https://api.example.com/test",
                        "method": "GET",
                    },
                }
            ]
        }
        tools = parse_tools(config)
        assert len(tools) == 1
        assert tools[0].name == "test_tool"
        assert tools[0].handler_type == HandlerType.REST
        assert tools[0].url == "https://api.example.com/test"
        assert tools[0].method == "GET"


class TestParseTools:
    def test_parse_rest_tool(self):
        config = {
            "tools": [
                {
                    "name": "get_data",
                    "description": "Get data",
                    "handler": {
                        "url": "https://api.example.com/data",
                        "method": "GET",
                    },
                }
            ]
        }
        tools = parse_tools(config)
        assert len(tools) == 1
        assert tools[0].handler_type == HandlerType.REST

    def test_parse_graphql_tool(self):
        config = {
            "tools": [
                {
                    "name": "graphql_query",
                    "description": "GraphQL query",
                    "handler": {
                        "type": "graphql",
                        "url": "https://api.example.com/graphql",
                        "query": "query { users { id } }",
                    },
                }
            ]
        }
        tools = parse_tools(config)
        assert len(tools) == 1
        assert tools[0].handler_type == HandlerType.GRAPHQL

    def test_parse_jsonrpc_tool(self):
        config = {
            "tools": [
                {
                    "name": "rpc_call",
                    "description": "JSONRPC call",
                    "handler": {
                        "type": "jsonrpc",
                        "url": "https://api.example.com/rpc",
                        "method": "getUser",
                    },
                }
            ]
        }
        tools = parse_tools(config)
        assert len(tools) == 1
        assert tools[0].handler_type == HandlerType.JSONRPC
        assert tools[0].jsonrpc_method == "getUser"

    def test_parse_tool_with_array_headers(self):
        config = {
            "tools": [
                {
                    "name": "api_call",
                    "description": "API call with headers",
                    "handler": {
                        "url": "https://api.example.com/api",
                        "method": "POST",
                        "headers": [
                            {"name": "Authorization", "value": "Bearer token"},
                            {"name": "X-Request-ID", "value": "123"},
                        ],
                    },
                }
            ]
        }
        tools = parse_tools(config)
        assert len(tools) == 1
        assert tools[0].headers == {
            "Authorization": "Bearer token",
            "X-Request-ID": "123",
        }

    def test_parse_tool_with_body(self):
        config = {
            "tools": [
                {
                    "name": "create_item",
                    "description": "Create item",
                    "handler": {
                        "url": "https://api.example.com/items",
                        "method": "POST",
                        "body": {"type": "default"},
                    },
                }
            ]
        }
        tools = parse_tools(config)
        assert len(tools) == 1
        assert tools[0].body == {"type": "default"}

    def test_parse_tool_with_dict_headers(self):
        config = {
            "tools": [
                {
                    "name": "api_call",
                    "description": "API call",
                    "handler": {
                        "url": "https://api.example.com/api",
                        "method": "GET",
                        "headers": {
                            "Authorization": "Bearer old-token",
                            "Content-Type": "application/json",
                        },
                    },
                }
            ]
        }
        tools = parse_tools(config)
        assert len(tools) == 1
        assert tools[0].headers == {
            "Authorization": "Bearer old-token",
            "Content-Type": "application/json",
        }


class TestToolDefinition:
    def test_tool_definition_creation(self):
        tool = ToolDefinition(
            name="test",
            description="Test tool",
            input_schema={"type": "object", "properties": {}},
            handler_type=HandlerType.REST,
            url="https://api.example.com",
            method="GET",
            headers={},
        )
        assert tool.name == "test"
        assert tool.handler_type == HandlerType.REST

    def test_tool_definition_optional_fields(self):
        tool = ToolDefinition(
            name="test",
            description="Test",
            input_schema={},
            handler_type=HandlerType.REST,
            url="https://api.example.com",
            method="GET",
            headers={},
            body={"key": "value"},
            graphql_query="query { }",
            jsonrpc_method="test",
        )
        assert tool.body == {"key": "value"}
        assert tool.graphql_query == "query { }"
        assert tool.jsonrpc_method == "test"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])