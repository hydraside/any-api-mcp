import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from any_api_mcp.loader import (
    create_tool,
    create_rest_tool,
    create_graphql_tool,
    create_jsonrpc_tool,
    ToolDefinition,
    HandlerType,
)


@pytest.fixture
def rest_tool_def():
    return ToolDefinition(
        name="get_users",
        description="Get users list",
        input_schema={
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Max results"}
            }
        },
        handler_type=HandlerType.REST,
        url="https://api.example.com/users",
        method="GET",
        headers={"Authorization": "Bearer token"},
    )


@pytest.fixture
def post_tool_def():
    return ToolDefinition(
        name="create_user",
        description="Create new user",
        input_schema={
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string"}
            },
            "required": ["name", "email"]
        },
        handler_type=HandlerType.REST,
        url="https://api.example.com/users",
        method="POST",
        headers={},
        body={"active": True},
    )


@pytest.fixture
def graphql_tool_def():
    return ToolDefinition(
        name="search_users",
        description="Search users via GraphQL",
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string"}
            }
        },
        handler_type=HandlerType.GRAPHQL,
        url="https://api.example.com/graphql",
        method="POST",
        headers={"Authorization": "Bearer token"},
        graphql_query="query ($query: String!) { searchUsers(query: $query) { id name } }",
        graphql_variables={"limit": 10},
    )


@pytest.fixture
def jsonrpc_tool_def():
    return ToolDefinition(
        name="get_user",
        description="Get user via JSONRPC",
        input_schema={
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"}
            },
            "required": ["user_id"]
        },
        handler_type=HandlerType.JSONRPC,
        url="https://api.example.com/rpc",
        method="POST",
        headers={},
        jsonrpc_method="getUser",
    )


class TestCreateRestTool:
    @pytest.mark.asyncio
    async def test_get_request_adds_query_params(self, rest_tool_def):
        tool = create_rest_tool(rest_tool_def)
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = [{"id": 1, "name": "John"}]
            mock_response.status_code = 200
            
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                return_value=mock_response
            )
            
            result = await tool(limit=10)
            
            assert result == [{"id": 1, "name": "John"}]
            
            call_args = mock_client.return_value.__aenter__.return_value.request.call_args
            assert call_args.kwargs["method"] == "GET"
            assert "limit=10" in call_args.kwargs["url"]

    @pytest.mark.asyncio
    async def test_post_request_with_body(self, post_tool_def):
        tool = create_rest_tool(post_tool_def)
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = {"id": 1, "name": "John", "email": "john@example.com", "active": True}
            mock_response.status_code = 201
            
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                return_value=mock_response
            )
            
            result = await tool(name="John", email="john@example.com")
            
            assert result["id"] == 1
            
            call_args = mock_client.return_value.__aenter__.return_value.request.call_args
            assert call_args.kwargs["method"] == "POST"
            assert call_args.kwargs["json"]["name"] == "John"
            assert call_args.kwargs["json"]["active"] == True

    @pytest.mark.asyncio
    async def test_request_uses_headers(self, rest_tool_def):
        tool = create_rest_tool(rest_tool_def)
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = []
            
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                return_value=mock_response
            )
            
            await tool()
            
            call_args = mock_client.return_value.__aenter__.return_value.request.call_args
            assert call_args.kwargs["headers"]["Authorization"] == "Bearer token"

    @pytest.mark.asyncio
    async def test_request_returns_text_on_invalid_json(self, rest_tool_def):
        tool = create_rest_tool(rest_tool_def)
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.side_effect = ValueError("Invalid JSON")
            mock_response.text = "Plain text response"
            mock_response.status_code = 200
            
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                return_value=mock_response
            )
            
            result = await tool()
            
            assert result == {"text": "Plain text response"}


class TestCreateGraphqlTool:
    @pytest.mark.asyncio
    async def test_graphql_query_with_variables(self, graphql_tool_def):
        tool = create_graphql_tool(graphql_tool_def)
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "data": {"searchUsers": [{"id": 1, "name": "John"}]}
            }
            
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                return_value=mock_response
            )
            
            result = await tool(query="John")
            
            assert "data" in result
            
            call_args = mock_client.return_value.__aenter__.return_value.request.call_args
            payload = call_args.kwargs["json"]
            assert "query" in payload
            assert payload["variables"]["query"] == "John"
            assert payload["variables"]["limit"] == 10

    @pytest.mark.asyncio
    async def test_graphql_uses_headers(self, graphql_tool_def):
        tool = create_graphql_tool(graphql_tool_def)
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = {"data": {}}
            
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                return_value=mock_response
            )
            
            await tool(query="test")
            
            call_args = mock_client.return_value.__aenter__.return_value.request.call_args
            assert call_args.kwargs["headers"]["Authorization"] == "Bearer token"


class TestCreateJsonrpcTool:
    @pytest.mark.asyncio
    async def test_jsonrpc_request_format(self, jsonrpc_tool_def):
        tool = create_jsonrpc_tool(jsonrpc_tool_def)
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "jsonrpc": "2.0",
                "result": {"id": 1, "name": "John"},
                "id": 1
            }
            
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                return_value=mock_response
            )
            
            result = await tool(user_id=1)
            
            assert result["result"]["id"] == 1
            
            call_args = mock_client.return_value.__aenter__.return_value.request.call_args
            payload = call_args.kwargs["json"]
            assert payload["jsonrpc"] == "2.0"
            assert payload["method"] == "getUser"
            assert payload["params"]["user_id"] == 1
            assert payload["id"] == 1


class TestCreateTool:
    def test_create_tool_returns_correct_handler_type(self, rest_tool_def, graphql_tool_def, jsonrpc_tool_def):
        rest_handler = create_tool(rest_tool_def)
        graphql_handler = create_tool(graphql_tool_def)
        jsonrpc_handler = create_tool(jsonrpc_tool_def)
        
        assert callable(rest_handler)
        assert callable(graphql_handler)
        assert callable(jsonrpc_handler)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])