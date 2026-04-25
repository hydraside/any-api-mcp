import yaml
import httpx
import re
import json
import logging
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum


logger = logging.getLogger("any_api_mcp")


class HandlerType(Enum):
    REST = "rest"
    GRAPHQL = "graphql"
    JSONRPC = "jsonrpc"
    SWAGGER = "swagger"


@dataclass
class AuthConfig:
    type: str = "none"  # none, api_key, bearer, basic, oauth2
    header: str = "Authorization"
    prefix: str = "Bearer"
    username: Optional[str] = None
    password: Optional[str] = None
    token_url: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    scopes: list = field(default_factory=list)
    _token: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "AuthConfig":
        auth = cls(type=data.get("type", "none"))
        auth.header = data.get("header", "Authorization")
        auth.prefix = data.get("prefix", "Bearer")
        auth.username = data.get("username")
        auth.password = data.get("password")
        auth.token_url = data.get("token_url")
        auth.client_id = data.get("client_id")
        auth.client_secret = data.get("client_secret")
        auth.scopes = data.get("scopes", [])
        return auth

    async def get_token(self) -> Optional[str]:
        if self._token:
            return self._token
        
        if self.type == "oauth2" and self.token_url:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    self.token_url,
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "scope": " ".join(self.scopes)
                    }
                )
                if resp.status_code == 200:
                    self._token = resp.json().get("access_token")
        return self._token

    def get_headers(self, static_token: Optional[str] = None) -> dict:
        headers = {}
        
        if self.type == "none":
            pass
        elif self.type == "api_key":
            headers[self.header] = static_token or ""
        elif self.type == "bearer":
            token = static_token or self._token or ""
            headers[self.header] = f"{self.prefix} {token}"
        elif self.type == "basic" and self.username:
            import base64
            creds = f"{self.username}:{self.password or ''}"
            headers[self.header] = f"Basic {base64.b64encode(creds.encode()).decode()}"
        elif self.type == "oauth2" and self._token:
            headers[self.header] = f"Bearer {self._token}"
        
        return headers


@dataclass
class ToolDefinition:
    name: str
    description: str
    input_schema: dict
    handler_type: HandlerType
    url: str
    method: str
    headers: dict
    body: Optional[dict] = None
    graphql_query: Optional[str] = None
    graphql_variables: Optional[dict] = None
    jsonrpc_method: Optional[str] = None
    operation_id: Optional[str] = None


def load_config(path: str) -> dict:
    import os
    
    if os.path.isabs(path):
        logger.debug(f"Loading config from absolute path: {path}")
        with open(path, "r") as f:
            config = yaml.safe_load(f)
        logger.info(f"Loaded config from {path}")
        return config
    
    search_paths = [
        path,
        os.path.join(os.getcwd(), path),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), path),
    ]
    
    for search_path in search_paths:
        if os.path.exists(search_path):
            logger.debug(f"Found config at: {search_path}")
            with open(search_path, "r") as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded config from {search_path}")
            return config
    
    with open(path, "r") as f:
        return yaml.safe_load(f)


def load_swagger(url: str, headers: dict = None) -> dict:
    response = httpx.get(url, headers=headers or {})
    return response.json()


def parse_swagger_operations(spec: dict, base_url: str, auth: AuthConfig) -> list[ToolDefinition]:
    tools = []
    servers = spec.get("servers", [])
    if servers and servers[0].get("url"):
        base_url = servers[0]["url"]
    
    paths = spec.get("paths", {})
    for path, methods in paths.items():
        for method, operation in methods.items():
            if method.upper() not in ("GET", "POST", "PUT", "PATCH", "DELETE"):
                continue
            
            op_id = operation.get("operationId") or operation.get("summary", path)
            name = re.sub(r"[^a-z0-9_]", "_", op_id.lower())
            
            properties = {}
            required_params = []
            
            params = operation.get("parameters", [])
            for param in params:
                p_name = param.get("name")
                p_required = param.get("required", False)
                p_schema = param.get("schema", {})
                p_type = p_schema.get("type", "string")
                
                properties[p_name] = {
                    "type": p_type,
                    "description": param.get("description", "")
                }
                if p_required:
                    required_params.append(p_name)
            
            request_body = operation.get("requestBody")
            if request_body:
                content = request_body.get("content", {})
                if "application/json" in content:
                    schema = content["application/json"].get("schema", {})
                    for prop, prop_data in schema.get("properties", {}).items():
                        properties[prop] = {
                            "type": prop_data.get("type", "string"),
                            "description": prop_data.get("description", "")
                        }
                    if schema.get("required"):
                        required_params.extend(schema["required"])
            
            tools.append(ToolDefinition(
                name=name,
                description=operation.get("description", operation.get("summary", "")),
                input_schema={
                    "type": "object",
                    "properties": properties,
                    "required": required_params
                },
                handler_type=HandlerType.REST,
                url=f"{base_url}{path}",
                method=method.upper(),
                headers={},
                operation_id=op_id
            ))
    
    return tools


def parse_insomnia_requests(data: dict, base_headers: dict = None) -> list[ToolDefinition]:
    tools = []
    base_headers = base_headers or {}
    
    resources = data.get("_resources", [])
    
    def flatten_items(items, parent_name=""):
        result = []
        for item in items:
            name = f"{parent_name}_{item['name']}" if parent_name else item['name']
            result.append((name, item))
            if item.get("items"):
                result.extend(flatten_items(item["items"], name))
        return result
    
    for resource in resources:
        if resource.get("_type") == "workspace":
            for item in resource.get("items", []):
                for name, req in flatten_items([item]):
                    if req.get("_type") != "request":
                        continue
                    
                    request = req.get("request", {})
                    method = request.get("method", "GET").upper()
                    url = request.get("url", "")
                    body = request.get("body", {})
                    
                    headers = dict(base_headers)
                    req_headers = request.get("headers", [])
                    for h in req_headers:
                        headers[h.get("name", "")] = h.get("value", "")
                    
                    body_data = None
                    if body.get("text"):
                        try:
                            body_data = json.loads(body["text"])
                        except Exception:
                            body_data = {"raw": body["text"]}
                    
                    tool_name = re.sub(r"[^a-z0-9_]", "_", name.lower())
                    
                    properties = {}
                    if body_data and isinstance(body_data, dict):
                        for key in body_data:
                            properties[key] = {"type": "string"}
                    
                    tools.append(ToolDefinition(
                        name=tool_name,
                        description=f"Insomnia request: {name}",
                        input_schema={"type": "object", "properties": properties},
                        handler_type=HandlerType.REST,
                        url=url,
                        method=method,
                        headers=headers,
                        body=body_data
                    ))
    
    return tools


def parse_tools(config: dict) -> list[ToolDefinition]:
    tools = []
    
    swagger = config.get("swagger")
    if swagger:
        spec_url = swagger.get("url", "")
        if spec_url:
            logger.info(f"Loading tools from Swagger: {spec_url}")
            auth = AuthConfig.from_dict(swagger.get("auth", {}))
            try:
                spec = load_swagger(spec_url, auth.get_headers(swagger.get("token")))
                base_url = swagger.get("base_url", "")
                swagger_tools = parse_swagger_operations(spec, base_url, auth)
                if swagger_tools:
                    logger.info(f"Generated {len(swagger_tools)} tools from Swagger")
                    return swagger_tools
            except Exception as e:
                logger.warning(f"Could not load Swagger: {e}")
    
    insomnia = config.get("insomnia")
    if insomnia:
        logger.info("Loading tools from Insomnia")
        import json
        try:
            if insomnia.get("file"):
                with open(insomnia["file"], "r") as f:
                    data = json.load(f)
            else:
                data = insomnia.get("data", {})
            
            headers = {}
            auth = AuthConfig.from_dict(insomnia.get("auth", {}))
            headers.update(auth.get_headers(insomnia.get("token")))
            
            insomnia_tools = parse_insomnia_requests(data, headers)
            if insomnia_tools:
                return insomnia_tools
        except Exception as e:
            print(f"Warning: Could not load Insomnia: {e}")
    
    for tool in config.get("tools", []):
        handler = tool.get("handler", {})
        handler_type = handler.get("type", "rest").lower()
        
        if handler_type == "graphql":
            graphql_headers = parse_headers(handler.get("headers", {}))
            tools.append(ToolDefinition(
                name=tool["name"],
                description=tool.get("description", ""),
                input_schema=tool.get("input_schema", {}),
                handler_type=HandlerType.GRAPHQL,
                url=handler.get("url", ""),
                method="POST",
                headers=graphql_headers,
                graphql_query=handler.get("query", ""),
                graphql_variables=handler.get("variables", {})
            ))
        elif handler_type == "jsonrpc":
            jsonrpc_headers = parse_headers(handler.get("headers", {}))
            tools.append(ToolDefinition(
                name=tool["name"],
                description=tool.get("description", ""),
                input_schema=tool.get("input_schema", {}),
                handler_type=HandlerType.JSONRPC,
                url=handler.get("url", ""),
                method="POST",
                headers=jsonrpc_headers,
                jsonrpc_method=handler.get("method", "")
            ))
        else:
            rest_headers = parse_headers(handler.get("headers", {}))
            tools.append(ToolDefinition(
                name=tool["name"],
                description=tool.get("description", ""),
                input_schema=tool.get("input_schema", {}),
                handler_type=HandlerType.REST,
                url=handler.get("url", ""),
                method=handler.get("method", "GET").upper(),
                headers=rest_headers,
                body=handler.get("body", {})
            ))
    logger.info(f"Loaded {len(tools)} tools from config")
    return tools


def parse_headers(headers) -> dict:
    if not headers:
        return {}
    if isinstance(headers, list):
        result = {}
        for h in headers:
            if isinstance(h, dict):
                result[h.get("name", "")] = h.get("value", "")
            elif isinstance(h, str):
                parts = h.split(":")
                if len(parts) >= 2:
                    result[parts[0].strip()] = ":".join(parts[1:]).strip()
        return result
    return headers if isinstance(headers, dict) else {}


def create_rest_tool(definition: ToolDefinition):
    async def tool(**kwargs) -> dict:
        url = definition.url
        method = definition.method.upper()
        
        body = definition.body or {}
        body.update(kwargs)
        
        if method == "GET" and kwargs:
            separator = "?" if "?" not in url else "&"
            query_params = "&".join(f"{k}={v}" for k, v in kwargs.items())
            url = f"{url}{separator}{query_params}"
            body = None
        
        logger.debug(f"{method} {url}")
        
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                headers=definition.headers,
                json=body
            )
            logger.debug(f"Response: {response.status_code}")
            try:
                return response.json()
            except Exception:
                return {"text": response.text}
    
    return tool


def create_graphql_tool(definition: ToolDefinition):
    async def tool(**kwargs) -> dict:
        variables = definition.graphql_variables or {}
        variables.update(kwargs)
        
        payload = {
            "query": definition.graphql_query,
            "variables": variables
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method="POST",
                url=definition.url,
                headers=definition.headers,
                json=payload
            )
            try:
                return response.json()
            except Exception:
                return {"text": response.text}
    
    return tool


def create_jsonrpc_tool(definition: ToolDefinition):
    async def tool(**kwargs) -> dict:
        payload = {
            "jsonrpc": "2.0",
            "method": definition.jsonrpc_method,
            "params": kwargs,
            "id": 1
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method="POST",
                url=definition.url,
                headers=definition.headers,
                json=payload
            )
            try:
                return response.json()
            except Exception:
                return {"text": response.text}
    
    return tool


def create_tool(definition: ToolDefinition):
    if definition.handler_type == HandlerType.GRAPHQL:
        return create_graphql_tool(definition)
    elif definition.handler_type == HandlerType.JSONRPC:
        return create_jsonrpc_tool(definition)
    else:
        return create_rest_tool(definition)