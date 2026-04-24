# any-api-mcp

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/fastmcp-2.0+-green.svg" alt="FastMCP">
  <img src="https://img.shields.io/badge/license-MIT-yellow.svg" alt="License">
</p>

> Dynamic MCP server that generates tools from YAML configuration. Define REST APIs once, use everywhere.

## Features

- **YAML-driven** — Define MCP tools in simple YAML files
- **REST-native** — Built for HTTP APIs (GET, POST, PUT, DELETE)
- **Zero code** — No Python needed to add new tools
- **FastMCP-powered** — Leverages the FastMCP framework
- **UV-managed** — Fast dependency management

## Why?

Typically you'd create MCP tools like this:

```python
from fastmcp import FastMCP

mcp = FastMCP("MyServer")

@mcp.tool()
def get_weather(city: str) -> dict:
    return requests.get(f"https://api.weather.com/{city}").json()
```

With **any-api-mcp**, you just write YAML:

```yaml
tools:
  - name: get_weather
    description: Get weather for a city
    input_schema:
      type: object
      properties:
        city:
          type: string
          description: City name
      required: [city]
    handler:
      url: https://api.weather.com/v1/forecast
      method: GET
```

That's it. No code changes needed.

## Install

```bash
# Clone and enter
git clone https://github.com/hydraside/any-api-mcp.git
cd any-api-mcp

# Install dependencies
uv sync
```

## Quick Start

### 1. Create your API config

```yaml
# my-api.yaml
server_name: weather-api
version: "1.0"

tools:
  - name: get_forecast
    description: Get weather forecast for a city
    input_schema:
      type: object
      properties:
        city:
          type: string
          description: City name (e.g., London, Tokyo)
      required:
        - city
    handler:
      url: https://api.weather.com/v1/forecast
      method: GET
      headers:
        Authorization: "Bearer YOUR_API_KEY"

  - name: search_cities
    description: Search for cities by name
    input_schema:
      type: object
      properties:
        q:
          type: string
          description: Search query
      required:
        - q
    handler:
      url: https://api.weather.com/v1/search
      method: GET
```

### 2. Run the server

```bash
CONFIG_PATH=my-api.yaml uv run python -m any_api_mcp.server
```

### 3. Connect to Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "my-weather-api": {
      "command": "uv",
      "args": ["run", "python", "-m", "any_api_mcp.server"],
      "env": {
        "CONFIG_PATH": "my-api.yaml"
      }
    }
  }
}
```

## Configuration Reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `server_name` | string | No | Server name shown in MCP |
| `version` | string | No | API version |
| `tools` | array | Yes | List of tool definitions |

### Tool Definition

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Tool name (snake_case) |
| `description` | string | Yes | Tool description |
| `input_schema` | object | Yes | JSON Schema for parameters |
| `handler.url` | string | Yes | REST endpoint URL |
| `handler.method` | string | No | GET, POST, PUT, DELETE (default: GET) |
| `handler.headers` | object | No | HTTP headers |

### Input Schema

Standard [JSON Schema](https://json-schema.org/) format:

```yaml
input_schema:
  type: object
  properties:
    param_name:
      type: string|number|integer|boolean
      description: Parameter description
      enum: [option1, option2]  # for enums
  required:
    - param_name
```

## Examples

### GET Request

```yaml
- name: get_users
  handler:
    url: https://api.example.com/users
    method: GET
```

### POST with Body

```yaml
- name: create_user
  input_schema:
    type: object
    properties:
      name:
        type: string
      email:
        type: string
    required: [name, email]
  handler:
    url: https://api.example.com/users
    method: POST
```

### With Headers

```yaml
- name: get_private_data
  handler:
    url: https://api.example.com/private
    method: GET
    headers:
      Authorization: "Bearer YOUR_TOKEN"
      X-API-Version: "2"
```

### With Fixed Body

```yaml
- name: create_webhook
  handler:
    url: https://api.example.com/webhooks
    method: POST
    body:
      type: "notification"
      enabled: true
```

### GraphQL

```yaml
- name: search_characters
  input_schema:
    type: object
    properties:
      name:
        type: string
        description: Character name to search
  handler:
    type: graphql
    url: https://api.example.com/graphql
    query: |
      query ($name: String!) {
        characters(filter: { name: $name }) {
          results {
            name
            status
          }
        }
      }
```

### JSONRPC

```yaml
- name: get_user
  input_schema:
    type: object
    properties:
      user_id:
        type: integer
      required: [user_id]
  handler:
    type: jsonrpc
    url: https://api.example.com/rpc
    method: getUser
```

## Install

### As CLI Tool

```bash
# From GitHub
pip install git+https://github.com/hydraside/any-api-mcp.git

# Run
any-api-mcp --help
```

### As Library

```python
from any_api_mcp import create_server

mcp = create_server("config.yaml")
mcp.run()
```

## Development

```bash
# Run tests
uv run pytest

# Lint
uv run ruff check .

# Format
uv run ruff format .
```

## Web UI

For a visual YAML configuration editor, see the separate repository:

**👉 [any-api-mcp-web](https://github.com/hydraside/any-api-mcp-web)**

```bash
git clone https://github.com/hydraside/any-api-mcp-web.git
cd any-api-mcp-web
npm install
npm run dev
```

## License

MIT — see [LICENSE](LICENSE) for details.