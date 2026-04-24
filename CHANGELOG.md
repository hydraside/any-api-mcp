# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Swagger/OpenAPI** — Generate tools from OpenAPI specs
- **Auth support** — api_key, bearer, basic, oauth2
- **Insomnia import** — Import from Insomnia Collections

## [0.2.0] - 2026-04-24

### Added

- **GraphQL support** — Define GraphQL queries in YAML
- **JSONRPC support** — Define JSONRPC methods in YAML  
- **Request body** — Support for fixed request body in REST handlers
- Multiple handler types: `rest`, `graphql`, `jsonrpc`

### Changed

- Refactored loader to support multiple handler types

## [0.1.0] - 2026-04-24

### Added

- Initial release
- REST API tool generation from YAML
- YAML configuration for MCP tools
- FastMCP server integration