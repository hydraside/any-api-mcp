import yaml
import os
import httpx
from typing import Any
from dataclasses import dataclass


@dataclass
class ToolDefinition:
    name: str
    description: str
    input_schema: dict
    url: str
    method: str
    headers: dict


def load_config(path: str) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def parse_tools(config: dict) -> list[ToolDefinition]:
    tools = []
    for tool in config.get("tools", []):
        handler = tool.get("handler", {})
        tools.append(ToolDefinition(
            name=tool["name"],
            description=tool.get("description", ""),
            input_schema=tool.get("input_schema", {}),
            url=handler.get("url", ""),
            method=handler.get("method", "GET"),
            headers=handler.get("headers", {})
        ))
    return tools


def create_rest_tool(definition: ToolDefinition):
    async def tool(**kwargs) -> dict:
        url = definition.url
        method = definition.method.upper()
        
        if method == "GET" and kwargs:
            separator = "&" if "?" in url else "?"
            query_params = "&".join(f"{k}={v}" for k, v in kwargs.items())
            url = f"{url}{separator}{query_params}"
        
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                headers=definition.headers,
                json=kwargs if method in ("POST", "PUT", "PATCH") else None
            )
            try:
                return response.json()
            except Exception:
                return {"text": response.text}
    
    return tool