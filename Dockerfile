FROM python:3.13-slim

LABEL maintainer="hydraside"
LABEL description="Dynamic MCP server with YAML configuration"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CONFIG_PATH=/app/config.yaml

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN pip install --no-cache-dir uv && \
    uv sync --frozen

COPY any_api_mcp ./any_api_mcp
COPY config.yaml ./

EXPOSE 8000

ENTRYPOINT ["any-api-mcp"]
CMD ["--help"]