import pytest
from any_api_mcp.server import create_server


class TestEndToEnd:
    @pytest.fixture
    def config_path(self, tmp_path):
        config = """
server_name: httpbin-test
version: "1.0"

tools:
  - name: get_headers
    description: Returns request headers
    input_schema:
      type: object
      properties: {}
    handler:
      url: https://httpbin.org/get
      method: GET

  - name: post_data
    description: Returns request data
    input_schema:
      type: object
      properties:
        name:
          type: string
          description: Your name
        email:
          type: string
          description: Your email
      required:
        - name
    handler:
      url: https://httpbin.org/post
      method: POST

  - name: echo_json
    description: Echoes JSON back
    input_schema:
      type: object
      properties:
        message:
          type: string
          description: Message to echo
        count:
          type: integer
          description: Count
      required:
        - message
    handler:
      url: https://httpbin.org/post
      method: POST
      body:
        source: any-api-mcp-test

  - name: get_ip
    description: Returns public IP
    input_schema:
      type: object
      properties: {}
    handler:
      url: https://httpbin.org/ip
      method: GET
"""
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text(config)
        return str(config_file)

    @pytest.mark.asyncio
    async def test_create_server_parses_config(self, config_path):
        mcp = create_server(config_path)
        assert mcp is not None

    @pytest.mark.asyncio
    async def test_get_request_real_httpbin(self, config_path):
        from any_api_mcp.loader import load_config, parse_tools, create_tool
        
        config = load_config(config_path)
        tools = parse_tools(config)
        
        get_headers_tool = next(t for t in tools if t.name == "get_headers")
        handler = create_tool(get_headers_tool)
        
        result = await handler()
        
        assert "headers" in result or "origin" in result

    @pytest.mark.asyncio
    async def test_post_request_real_httpbin(self, config_path):
        from any_api_mcp.loader import load_config, parse_tools, create_tool
        
        config = load_config(config_path)
        tools = parse_tools(config)
        
        post_tool = next(t for t in tools if t.name == "post_data")
        handler = create_tool(post_tool)
        
        result = await handler(name="Test", email="test@example.com")
        
        assert result.get("json") is not None or result.get("form") is not None
        data = result.get("json", {})
        assert data.get("name") == "Test"
        assert data.get("email") == "test@example.com"

    @pytest.mark.asyncio
    async def test_echo_with_fixed_body(self, config_path):
        from any_api_mcp.loader import load_config, parse_tools, create_tool
        
        config = load_config(config_path)
        tools = parse_tools(config)
        
        echo_tool = next(t for t in tools if t.name == "echo_json")
        handler = create_tool(echo_tool)
        
        result = await handler(message="hello", count=42)
        
        data = result.get("json", {})
        assert data.get("message") == "hello"
        assert data.get("count") == 42
        assert data.get("source") == "any-api-mcp-test"

    @pytest.mark.asyncio
    async def test_get_ip(self, config_path):
        from any_api_mcp.loader import load_config, parse_tools, create_tool
        
        config = load_config(config_path)
        tools = parse_tools(config)
        
        ip_tool = next(t for t in tools if t.name == "get_ip")
        handler = create_tool(ip_tool)
        
        result = await handler()
        
        assert "origin" in result


class TestGraphQLEndToEnd:
    @pytest.fixture
    def config_path(self, tmp_path):
        config = """
server_name: graphql-test
version: "1.0"

tools:
  - name: search_character
    description: Search Rick and Morty characters
    input_schema:
      type: object
      properties:
        name:
          type: string
          description: Character name
      required:
        - name
    handler:
      type: graphql
      url: https://rickandmortyapi.com/graphql
      query: |
        query ($name: String!) {
          characters(filter: { name: $name }) {
            results {
              name
              status
              species
            }
          }
        }
"""
        config_file = tmp_path / "graphql_config.yaml"
        config_file.write_text(config)
        return str(config_file)

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_graphql_real_api(self, config_path):
        from any_api_mcp.loader import load_config, parse_tools, create_tool
        
        config = load_config(config_path)
        tools = parse_tools(config)
        
        char_tool = next(t for t in tools if t.name == "search_character")
        handler = create_tool(char_tool)
        
        result = await handler(name="Rick")
        
        assert "data" in result
        characters = result["data"]["characters"]["results"]
        assert len(characters) > 0
        assert "Rick" in characters[0]["name"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])