# PerfEng Platform

Core orchestration and analysis platform for continuous performance engineering.

## Development

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Run linting
uv run ruff check .

# Run type checking
uv run mypy .

# Start API server
uv run uvicorn perfeng.api.main:app --reload

# Use CLI
uv run perfeng --help
```
