# ============================================================================
# CONSTRUCTURE RAG - MULTI-STAGE DOCKERFILE
# ============================================================================
# Targets:
#   - builder   : TDD gate (runs tests, build fails if tests fail)
#   - runtime   : Production FastAPI server
#   - streamlit : Test UI for interactive testing
#
# Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
# ============================================================================

# ============================================================================
# BASE STAGE - Shared dependencies
# ============================================================================
FROM python:3.12-slim AS base

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install UV package manager (fast, modern)
RUN pip install --no-cache-dir uv

# ============================================================================
# BUILDER STAGE - TDD Gate
# ============================================================================
FROM base AS builder

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

# Copy dependency files (cached layer)
COPY pyproject.toml uv.lock* README.md ./

# Install ALL dependencies including dev (for testing)
RUN uv venv .venv && \
    . .venv/bin/activate && \
    uv pip install -e ".[dev]"

# Copy source, tests, and test assets
COPY src/ ./src/
COPY tests/ ./tests/
COPY Assets/ ./Assets/

# TDD GATE: Build fails if tests fail
# Skip slow tests in CI (they parse actual PDFs and take longer)
RUN . .venv/bin/activate && pytest tests/ -v --tb=short -m "not slow"

# Lint check (non-blocking)
RUN . .venv/bin/activate && ruff check src/ || true

# ============================================================================
# RUNTIME STAGE - Production FastAPI
# ============================================================================
FROM base AS runtime

# Install minimal runtime dependencies (curl for healthcheck)
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml uv.lock* README.md ./

# Install production dependencies only
RUN uv venv .venv && \
    . .venv/bin/activate && \
    uv pip install -e "."

# Copy application source
COPY src/ ./src/

# Set PATH
ENV PATH="/app/.venv/bin:$PATH"

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Healthcheck using the API health endpoint
HEALTHCHECK --interval=10s --timeout=3s --start-period=15s --retries=3 \
    CMD curl -sf http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ============================================================================
# STREAMLIT STAGE - Test UI (Full-featured with local processing)
# ============================================================================
FROM base AS streamlit

# Install curl for healthcheck
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml uv.lock* README.md ./

# Install ALL dependencies (needed for local PDF processing)
RUN uv venv .venv && \
    . .venv/bin/activate && \
    uv pip install -e "." && \
    uv pip install streamlit httpx

# Copy source code AND streamlit app
COPY src/ ./src/
COPY streamlit_app.py ./

# Set PATH and PYTHONPATH so 'src' module is importable
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app"

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8501

HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -sf http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "streamlit_app.py", "--server.address", "0.0.0.0", "--server.port", "8501"]
