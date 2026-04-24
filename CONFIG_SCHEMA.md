# YAML Configuration Reference

Complete reference for `any-api-mcp` YAML configuration format.

## File Structure

```yaml
server_name: My Server      # Server name (optional)
version: "1.0"           # API version (optional)

swagger:                  # OR generate from Swagger/OpenAPI
  url: https://api.example.com/swagger.json
  ...

tools:                    # List of tools (required)
  - name: ...            # Tool definition
    ...
```

## Root Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `server_name` | string | No | Name displayed in MCP client |
| `version` | string | No | API version string |
| `swagger` | object | No | Generate tools from Swagger spec |
| `tools` | array | Yes | List of tool definitions |

## Tool Definition

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Tool name (snake_case, unique) |
| `description` | string | Yes | Tool description |
| `input_schema` | object | Yes | JSON Schema for parameters |
| `handler` | object | Yes | Handler configuration |

## Input Schema

Standard [JSON Schema](https://json-schema.org/) format:

```yaml
input_schema:
  type: object
  properties:
    param_name:
      type: string       # string, number, integer, boolean
      description: Description
      enum: [a, b]     # Allowed values
      default: value   # Default value
    optional_param:
      type: string
  required: [param_name]  # Required parameters
```

### Types

- `string` — Text values
- `number` — Floating point numbers
- `integer` — Integer numbers
- `boolean` — true/false

## Handler Configuration

### REST Handler (default)

```yaml
handler:
  type: rest           # Optional, "rest" is default
  url: https://api.example.com/endpoint
  method: GET         # GET, POST, PUT, PATCH, DELETE
  headers:           # Optional HTTP headers
    Authorization: "Bearer TOKEN"
    Content-Type: "application/json"
  body:              # Optional fixed body
    key: value
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | No | Handler type: `rest`, `graphql`, `jsonrpc` |
| `url` | string | Yes | REST endpoint URL |
| `method` | string | No | HTTP method (default: GET) |
| `headers` | object | No | HTTP headers |
| `body` | object | No | Fixed request body |

### GraphQL Handler

```yaml
handler:
  type: graphql
  url: https://api.example.com/graphql
  headers:
    Authorization: "Bearer TOKEN"
  query: |
    query ($name: String!) {
      characters(filter: { name: $name }) {
        results {
          name
          status
        }
      }
    }
  variables:          # Optional static variables
    limit: 10
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | Must be `graphql` |
| `url` | string | Yes | GraphQL endpoint URL |
| `headers` | object | No | HTTP headers |
| `query` | string | Yes | GraphQL query |
| `variables` | object | No | Static variables |

### JSONRPC Handler

```yaml
handler:
  type: jsonrpc
  url: https://api.example.com/rpc
  headers:
    Authorization: "Bearer TOKEN"
  method: getUser    # JSONRPC method name
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | Must be `jsonrpc` |
| `url` | string | Yes | JSONRPC endpoint URL |
| `headers` | object | No | HTTP headers |
| `method` | string | Yes | Method name |

## Swagger/OpenAPI

Generate tools automatically from an OpenAPI/Swagger specification:

```yaml
swagger:
  url: https://api.example.com/swagger.json
  base_url: https://api.example.com
  auth:
    type: bearer
    token: your-token
```

### Auth Types

| Type | Description |
|------|-------------|
| `none` | No authentication |
| `api_key` | API key in header |
| `bearer` | Bearer token (default) |
| `basic` | Basic auth |
| `oauth2` | OAuth2 client credentials |

### Auth Configuration

```yaml
# API Key
swagger:
  url: https://api.example.com/swagger.json
  auth:
    type: api_key
    header: X-API-Key
    token: your-key

# Bearer Token
swagger:
  url: https://api.example.com/swagger.json
  auth:
    type: bearer
    token: your-token

# OAuth2 Client Credentials
swagger:
  url: https://api.example.com/swagger.json
  auth:
    type: oauth2
    token_url: https://oauth.example.com/token
    client_id: your-client-id
    client_secret: your-client-secret
    scopes: [read, write]
```

| Field | Type | Description |
|-------|------|-------------|
| `url` | string | Swagger/OpenAPI spec URL |
| `base_url` | string | Base URL for API (optional) |
| `auth.type` | string | Auth type: none, api_key, bearer, basic, oauth2 |
| `auth.header` | string | Header name (default: Authorization) |
| `auth.prefix` | string | Token prefix (default: Bearer) |
| `auth.token` | string | Static token |
| `auth.username` | string | Username for basic auth |
| `auth.password` | string | Password for basic auth |
| `auth.token_url` | string | OAuth2 token endpoint |
| `auth.client_id` | string | OAuth2 client ID |
| `auth.client_secret` | string | OAuth2 client secret |
| `auth.scopes` | array | OAuth2 scopes |

## Insomnia

Import requests from Insomnia Collections:

```yaml
insomnia:
  file: ./insomnia-export.json
  auth:
    type: bearer
    token: your-token
```

| Field | Type | Description |
|-------|------|-------------|
| `file` | string | Path to Insomnia JSON export |
| `data` | object | Inline Insomnia data |
| `auth` | object | Auth configuration (same as Swagger) |
| `token` | string | Static token |

## Examples

### Complete REST Example

```yaml
server_name: Weather API
version: "2.0"

tools:
  - name: get_forecast
    description: Get weather forecast for a city
    input_schema:
      type: object
      properties:
        city:
          type: string
          description: City name (e.g., London, Paris)
        days:
          type: integer
          description: Number of days (1-7)
          default: 3
      required: [city]
    handler:
      url: https://api.weather.com/v2/forecast
      method: GET
      headers:
        X-API-Key: "YOUR_KEY"
      body:
        units: metric
```

### Complete GraphQL Example

```yaml
tools:
  - name: search_characters
    description: Search Rick and Morty characters
    input_schema:
      type: object
      properties:
        name:
          type: string
          description: Character name to search
        status:
          type: string
          enum: [alive, dead, unknown]
      required: [name]
    handler:
      type: graphql
      url: https://rickandmortyapi.com/graphql
      query: |
        query ($name: String!, $status: String) {
          characters(filter: { name: $name, status: $status }) {
            results {
              id
              name
              status
              species
              image
            }
          }
        }
```

### Multiple Tools

```yaml
server_name: My API
version: "1.0"

tools:
  - name: list_users
    description: Get all users
    input_schema:
      type: object
      properties: {}
    handler:
      url: https://api.example.com/users
      method: GET

  - name: create_user
    description: Create a new user
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

  - name: delete_user
    description: Delete a user by ID
    input_schema:
      type: object
      properties:
        user_id:
          type: integer
      required: [user_id]
    handler:
      url: https://api.example.com/users
      method: DELETE

  - name: get_stats
    description: Get user statistics via GraphQL
    input_schema:
      type: object
      properties:
        user_id:
          type: integer
      required: [user_id]
    handler:
      type: graphql
      url: https://api.example.com/graphql
      query: |
        query ($userId: Int!) {
          user(id: $userId) {
            name
            stats {
              posts
              followers
              following
            }
          }
        }

  - name: rpc_get_user
    description: Get user via JSONRPC
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

## Environment Variables

Use environment variables in your config:

```yaml
tools:
  - name: get_data
    handler:
      url: ${API_BASE_URL}/data
      headers:
        Authorization: "Bearer ${API_TOKEN}"
```

Set via environment or `.env` file:

```bash
export API_BASE_URL=https://api.example.com
export API_TOKEN=your_token
```