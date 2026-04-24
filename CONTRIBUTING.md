# Contributing to any-api-mcp

Thank you for considering contributing!

## How to Contribute

### Reporting Bugs

1. Check existing [issues](https://github.com/hydraside/any-api-mcp/issues) first
2. Open a new issue with:
   - Clear title
   - Steps to reproduce
   - Expected vs actual behavior
   - Your config.yaml (sanitized)

### Suggesting Features

1. Open a discussion or issue
2. Describe the use case
3. Propose the YAML structure

### Pull Requests

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Test locally: `uv sync && uv run python -m any_api_mcp.server`
5. Commit with clear messages
6. Push and open a PR

## Development Setup

```bash
# Clone
git clone https://github.com/hydraside/any-api-mcp.git
cd any-api-mcp

# Install dev dependencies
uv sync

# Run tests
uv run pytest

# Lint
uv run ruff check .
```

## Code Style

- Use [Ruff](https://docs.astral.sh/ruff/) for linting
- Type hints required
- Follow existing patterns in the codebase

## YAML Schema

When adding new handler types, update:

- `config.yaml` — example
- `loader.py` — parser
- Documentation in README

## License

By contributing, you agree that your contributions will be licensed under MIT.