import yaml
import httpx
from typing import Any, Optional
from dataclasses import dataclass
from enum import Enum


class HandlerType(Enum):
    REST = "rest"
    GRAPHQL = "graphql"
    JSONRPC = "jsonrpc"


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


def load_config(path: str) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def parse_tools(config: dict) -> list[ToolDefinition]:
    tools = []
    for tool in config.get("tools", []):
        handler = tool.get("handler", {})
        handler_type = handler.get("type", "rest").lower()
        
        if handler_type == "graphql":
            tools.append(ToolDefinition(
                name=tool["name"],
                description=tool.get("description", ""),
                input_schema=tool.get("input_schema", {}),
                handler_type=HandlerType.GRAPHQL,
                url=handler.get("url", ""),
                method="POST",
                headers=handler.get("headers", {}),
                graphql_query=handler.get("query", ""),
                graphql_variables=handler.get("variables", {})
            ))
        elif handler_type == "jsonrpc":
            tools.append(ToolDefinition(
                name=tool["name"],
                description=tool.get("description", ""),
                input_schema=tool.get("input_schema", {}),
                handler_type=HandlerType.JSONRPC,
                url=handler.get("url", ""),
                method="POST",
                headers=handler.get("headers", {}),
                jsonrpc_method=handler.get("method", "")
            ))
        else:
            tools.append(ToolDefinition(
                name=tool["name"],
                description=tool.get("description", ""),
                input_schema=tool.get("input_schema", {}),
                handler_type=HandlerType.REST,
                url=handler.get("url", ""),
                method=handler.get("method", "GET").upper(),
                headers=handler.get("headers", {}),
                body=handler.get("body", {})
            ))
    return tools


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
        
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                headers=definition.headers,
                json=body
            )
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