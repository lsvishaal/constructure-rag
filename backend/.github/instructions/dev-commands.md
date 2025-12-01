---
applyTo: '**'
---

# Development Commands - Always Use UV

This project uses **UV** as the Python package manager. Always use UV for all Python operations.

## Common Commands

```bash
# Install dependencies
uv sync --all-extras

# Run tests
uv run pytest -v

# Run tests with coverage
uv run pytest --cov=src --cov-report=term-missing

# Run specific test file
uv run pytest tests/unit/test_auth.py -v

# Start FastAPI server
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Start Streamlit demo
uv run streamlit run streamlit_app.py

# Run evaluation script
uv run python scripts/run_evaluation.py

# Add a new dependency
uv add <package-name>

# Add a dev dependency
uv add --dev <package-name>
```

## Environment Setup

```bash
# Create/sync virtual environment
uv sync

# Activate environment (optional, uv run handles this)
source .venv/bin/activate
```

## Docker Services

```bash
# Start Qdrant vector database
docker-compose up -d qdrant

# Start Ollama LLM server
docker-compose up -d ollama

# Pull LLM model
docker exec constructure-ollama ollama pull llama3.2:1b

# Start all services
docker-compose up -d
```

## Never Use

- ❌ `pip install` - Use `uv add` instead
- ❌ `python -m pytest` - Use `uv run pytest` instead
- ❌ `python script.py` - Use `uv run python script.py` instead
