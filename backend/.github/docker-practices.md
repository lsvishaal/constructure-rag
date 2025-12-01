# Docker Best Practices for FastAPI PR Review Agent

**Production-Grade Setup with Minimal Image Size & Fast Builds**

Based on Docker Image Best Practices (From 1.2GB to 10MB video analysis)

---

## Core Docker Optimization Principles

### 1. Multi-Stage Builds (Foundation)

Split your Dockerfile into multiple stages:
- **Stage 1 (Builder)**: Includes all build tools, dependencies, test runners.
- **Stage 2 (Runtime)**: Only production runtime and application code.

**Benefit**: Final image excludes build artifacts, reducing size from ~1GB to ~50MB or less.

```dockerfile
# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /build

# Install UV in builder
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Use UV to install dependencies into a venv
RUN uv venv .venv && \
    .venv/bin/uv pip install -r <(uv pip compile pyproject.toml)

# Copy source and run tests/lint
COPY . .
RUN .venv/bin/pytest tests/ && \
    .venv/bin/ruff check . && \
    .venv/bin/black --check .

# Stage 2: Runtime (Minimal)
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy only the venv from builder (not source or tools)
COPY --from=builder /build/.venv /app/.venv

# Copy only necessary source files (not tests, docs, etc.)
COPY src/ ./src/
COPY pyproject.toml ./

# Set PATH to use venv
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Use non-root user (security + compliance)
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')" || exit 1

# Run app
CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Why each part matters**:
- **Slim base**: `python:3.11-slim` instead of `python:3.11` removes docs, apt cache (saves 200MB).
- **Builder stage**: Installs UV and dependencies once; not carried to final image.
- **COPY venv only**: Copy the compiled venv, not source or pip caches.
- **COPY src/ only**: Don't copy tests, README, Dockerfile into image.
- **ENV variables**: `PYTHONUNBUFFERED` ensures logs appear immediately; `PYTHONDONTWRITEBYTECODE` skips `.pyc` files.
- **Non-root user**: Improves security (containers shouldn't run as root).
- **Healthcheck**: Allows orchestrators (Docker Compose, k8s) to detect dead services.

---

## 2. Layer Squashing & Minimization

Docker builds layers for each instruction. Each layer increases final size.

### Good Layer Strategy

```dockerfile
# ❌ Bad: Each RUN creates a layer
RUN pip install package1
RUN pip install package2
RUN pip install package3

# ✅ Good: Single RUN combines operations
RUN pip install package1 package2 package3

# ❌ Bad: Multiple copy operations create layers
COPY requirements.txt .
COPY src/ ./src/
COPY config/ ./config/

# ✅ Good: Combine, but order by change frequency
# (stable dependencies first, code changes last)
COPY pyproject.toml uv.lock* ./
COPY src/ ./src/
```

### Leverage Docker Cache

Docker caches layers based on instruction + file hash. **Order matters**:

```dockerfile
# ✅ Good: Stable deps first, source code last
FROM python:3.11-slim

WORKDIR /app

# Deps rarely change → cached if pyproject.toml unchanged
COPY pyproject.toml uv.lock* ./
RUN uv venv .venv && .venv/bin/uv pip install ...

# Source code changes frequently → invalidates cache
COPY src/ ./src/

CMD ["uvicorn", "src.app.main:app"]
```

**Build time impact**: Rebuilding after source change = ~2 sec (deps cached). Rebuilding after deps change = full install (~10–30 sec).

---

## 3. `.dockerignore` (Exclude Unnecessary Files)

Similar to `.gitignore`, prevents unnecessary files from being copied into build context.

```
# .dockerignore

# Version control
.git/
.gitignore

# Python artifacts
__pycache__/
*.py[cod]
*$py.class
*.egg-info/
.pytest_cache/
.mypy_cache/
.ruff_cache/

# Development
.venv/
venv/
.env
.env.local

# Testing
tests/
pytest.ini
coverage/

# Documentation
docs/
*.md
!README.md

# IDE
.vscode/
.idea/
*.swp
*.swo

# Misc
.DS_Store
*.log
node_modules/
```

**Impact**: Reduces build context size (Docker sends files to daemon), speeds up builds by 10–50%.

---

## 4. Base Image Selection

| Image | Size | Best For | Notes |
|-------|------|----------|-------|
| `python:3.11-slim` | ~150MB | FastAPI, most apps | Best ROI: includes basics, not bloated |
| `python:3.11-alpine` | ~100MB | Ultra-lean | Alpine missing glibc; C dependencies may fail |
| `distroless/python3.11` | ~70MB | Pure prod deployments | No shell, minimal attack surface; debug harder |
| `python:3.11` | ~900MB | Dev only | Includes compilers, apt, docs; never for prod |

**Recommendation for this project**: Use `python:3.11-slim` for builder and runtime. If you need to strip further, use `distroless/python3.11` for runtime after validation.

---

## 5. Dependency Management with UV

UV's lockfile ensures reproducible builds (same exact versions every run).

```dockerfile
# Copy both pyproject.toml and uv.lock
COPY pyproject.toml uv.lock* ./

# Install using lock file (faster, reproducible)
RUN uv venv .venv && \
    .venv/bin/uv pip install --frozen --no-cache
```

**Why `--frozen`**: Prevents random version updates; exact reproducibility.

---

## 6. Runtime Optimization

### Single Process vs. Workers

For a 2–3 day prototype, **single-process uvicorn is fine**:

```dockerfile
CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- Single process + async = handles hundreds of concurrent requests.
- Multiple workers add complexity (process management, shared state).
- Only scale if benchmarking shows single process is bottleneck.

### Environment Variables (No Secrets in Image)

```dockerfile
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LOG_LEVEL=info

# Secrets come from Docker Compose / env file at runtime
# NOT baked into Dockerfile
```

---

## 7. Logging & Output

**Always log to stdout/stderr** in Docker; Docker daemon captures it.

```dockerfile
# ✅ Correct: Uvicorn logs to stdout automatically
CMD ["uvicorn", "src.app.main:app"]

# ❌ Wrong: Logging to file means logs disappear
# CMD ["uvicorn", "src.app.main:app", "--log-config", "log_config.yaml"]
```

---

## Complete Production-Grade Dockerfile

```dockerfile
# ========================================
# Stage 1: Builder
# ========================================
FROM python:3.11-slim AS builder

WORKDIR /build

# Install UV package manager
RUN pip install uv

# Copy dependency files (cached if unchanged)
COPY pyproject.toml uv.lock* ./

# Create venv and install dependencies
# UV is much faster than pip; --frozen ensures reproducibility
RUN uv venv .venv && \
    .venv/bin/uv pip install --frozen --no-cache \
        -e ".[dev]" && \
    .venv/bin/pip cache purge

# Copy source code
COPY src/ ./src/
COPY tests/ ./tests/

# Run tests and linting
RUN .venv/bin/pytest tests/ -q && \
    .venv/bin/ruff check src/ && \
    .venv/bin/black --check src/

# ========================================
# Stage 2: Runtime (Minimal)
# ========================================
FROM python:3.11-slim AS runtime

WORKDIR /app

# Install curl for health checks (minimal)
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy venv from builder (compiled dependencies, no build tools)
COPY --from=builder /build/.venv /app/.venv

# Copy application source (not tests, not tools)
COPY src/ ./src/
COPY pyproject.toml ./

# Environment variables
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LOG_LEVEL=info \
    PORT=8000

# Security: Run as non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Health check (allows Docker/k8s to detect failures)
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port (documentation only; actual binding in CMD)
EXPOSE 8000

# Run FastAPI app with uvicorn
CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Expected final image size**: ~250–350MB (slim Python + deps, no build tools).

---

## Docker Compose Setup (Local Dev + Monitoring)

```yaml
# docker-compose.yml

version: '3.9'

services:
  # FastAPI Backend
  api:
    build:
      context: .
      dockerfile: Dockerfile
      target: runtime
    container_name: pr-review-api
    ports:
      - "8000:8000"
    environment:
      - LOG_LEVEL=debug
      - GITHUB_TOKEN=${GITHUB_TOKEN}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./src:/app/src:ro  # Hot reload for dev (remove for prod)
    depends_on:
      prometheus:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 15s

  # Prometheus (metrics scraper)
  prometheus:
    image: prom/prometheus:latest
    container_name: pr-review-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - "--config.file=/etc/prometheus/prometheus.yml"
      - "--storage.tsdb.path=/prometheus"
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:9090/-/healthy"]
      interval: 10s
      timeout: 5s
      retries: 3

  # Grafana (visualization)
  grafana:
    image: grafana/grafana:latest
    container_name: pr-review-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_INSTALL_PLUGINS=grafana-piechart-panel
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana-dashboards:/etc/grafana/provisioning/dashboards:ro
      - ./grafana-datasources.yml:/etc/grafana/provisioning/datasources/datasources.yml:ro
    depends_on:
      - prometheus
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/api/health"]
      interval: 10s
      timeout: 5s
      retries: 3

volumes:
  prometheus_data:
  grafana_data:
```

### Prometheus Config

```yaml
# prometheus.yml

global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'fastapi'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'
```

---

## Build & Run Commands

```bash
# Build image (multi-stage, only runtime stage tagged)
docker build -t pr-review-agent:latest .

# Build with no cache (if deps changed)
docker build --no-cache -t pr-review-agent:latest .

# Check image size
docker images | grep pr-review-agent

# Run full stack (API + Prometheus + Grafana)
docker-compose up --build

# View logs
docker-compose logs -f api

# Run specific service
docker-compose up api prometheus grafana

# Stop and clean
docker-compose down -v
```

---

## Performance Checklist

- [ ] Multi-stage Dockerfile (builder + runtime).
- [ ] Final image <500MB (target <300MB).
- [ ] `.dockerignore` excludes tests, docs, venv, cache.
- [ ] `python:3.11-slim` base (not full Python image).
- [ ] Non-root user (security).
- [ ] Healthcheck configured (enables orchestration).
- [ ] Dependencies cached (pyproject.toml + uv.lock stable, source last).
- [ ] Logs to stdout/stderr (no file logging in container).
- [ ] Environment variables externalized (no secrets in image).
- [ ] docker-compose includes monitoring (Prometheus + Grafana).

---

## Speed Benchmarks

| Operation | Time | Notes |
|-----------|------|-------|
| Build (cold, no cache) | ~30–60s | UV + tests + lint |
| Build (hot, cached) | ~2–5s | Only source layer changed |
| Build (deps only changed) | ~15–30s | Full install + tests |
| Startup (container to ready) | ~3–5s | FastAPI async startup |
| Image pull (first time) | ~20–40s | ~250MB image |
| Image pull (cached) | <1s | Already local |

This setup is **production-ready** with minimal overhead for a 2–3 day challenge.

