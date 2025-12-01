# 🏗️ Constructure RAG - Backend

> FastAPI-powered RAG system for construction document intelligence

---

## Quick Start

```bash
# Start all services (Qdrant, Ollama, FastAPI, Streamlit)
docker-compose up -d

# Or for local development:
uv sync --all-extras
uv run uvicorn src.main:app --reload --port 8000
```

**Services:**
| Service | URL | Purpose |
|---------|-----|---------|
| FastAPI | http://localhost:8000 | REST API |
| API Docs | http://localhost:8000/docs | Swagger UI |
| Streamlit | http://localhost:8501 | Demo UI with progress |
| Qdrant | http://localhost:6333 | Vector database |
| Ollama | http://localhost:11434 | LLM inference |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       INGESTION PIPELINE                         │
│  PDF ──► FastParser ──► Chunker ──► Embeddings ──► Qdrant       │
│       (PyMuPDF 30pg/s) (300w/75)  (BGE-small)    (384 dims)     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        QUERY PIPELINE                            │
│  Query ──► Cache? ──► Retrieval ──► RAG ──► Ollama ──► Response │
│            (LRU)     (cosine sim)  (prompt) (llama3.2)  +sources│
└─────────────────────────────────────────────────────────────────┘
```

### Service Components

| Service | File | Purpose |
|---------|------|---------|
| `fast_parser.py` | PDF Parsing | PyMuPDF @ 30 pages/sec |
| `chunking.py` | Text Chunking | 300 words, 75 overlap, structure-aware |
| `embeddings.py` | Vector Generation | BGE-small-en-v1.5, 384 dimensions |
| `vector_store.py` | Storage | Qdrant with cosine similarity |
| `retrieval.py` | Search | Top-K retrieval with scoring |
| `rag_pipeline.py` | RAG Orchestration | LLM prompting + caching |
| `extraction.py` | Structured Output | Door schedules, wage tables |
| `evaluation.py` | Testing | 10 queries, automatic scoring |
| `cache.py` | Response Cache | LRU + 1hr TTL |
| `auth.py` | Authentication | JWT + Argon2 password hashing |

---

## API Endpoints

### Authentication
```bash
# Login (OAuth2 form)
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testingcheckuser1234@gmail.com&password=constructure2024"

# Response: { "access_token": "...", "token_type": "bearer" }

# Get current user
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <token>"
```

### Documents
```bash
# Upload PDF
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@document.pdf"

# Bulk ingest from Assets/
curl -X POST http://localhost:8000/api/v1/documents/ingest \
  -H "Authorization: Bearer <token>"

# List documents
curl http://localhost:8000/api/v1/documents \
  -H "Authorization: Bearer <token>"

# Clear all documents
curl -X DELETE http://localhost:8000/api/v1/documents/clear \
  -H "Authorization: Bearer <token>"
```

### Chat (RAG)
```bash
# Q&A mode (default)
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the plumber wage rate?", "mode": "qa"}'

# Extraction mode
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"query": "Generate door schedule", "mode": "extraction"}'

# Sources only mode
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"query": "fire rating", "mode": "sources_only"}'
```

### Evaluation
```bash
# Get test queries
curl http://localhost:8000/api/v1/evaluation/queries \
  -H "Authorization: Bearer <token>"

# Run evaluation
curl -X POST http://localhost:8000/api/v1/evaluation/run \
  -H "Authorization: Bearer <token>"
```

---

## Streamlit Demo UI

The Streamlit app provides a visual interface with:
- **PDF Upload** with real-time progress tracking
- **Chunking Progress** - see pages parsed per second
- **Indexing Progress** - watch chunks being embedded
- **Interactive Chat** - same RAG functionality as API
- **Source Display** - expandable citations

```bash
# Start Streamlit (included in docker-compose)
uv run streamlit run streamlit_app.py
```

Features:
- Progress bars for parsing, chunking, and embedding
- Mode selector (qa, extraction, sources_only)
- Session state for chat history
- Document stats display

---

## Project Structure

```
backend/
├── src/
│   ├── api/                 # FastAPI route handlers
│   │   ├── auth.py          # JWT authentication
│   │   ├── chat.py          # RAG query endpoint
│   │   ├── documents.py     # Upload & ingestion
│   │   ├── evaluation.py    # Test harness
│   │   └── health.py        # Health checks
│   ├── core/
│   │   └── config.py        # Settings & watermarks
│   ├── models/
│   │   ├── auth.py          # User, Token schemas
│   │   ├── chat.py          # Request/Response models
│   │   ├── documents.py     # Document models
│   │   └── extraction.py    # Structured output schemas
│   └── services/
│       ├── auth.py          # Auth business logic
│       ├── fast_parser.py   # PyMuPDF parser
│       ├── chunking.py      # Text chunking
│       ├── embeddings.py    # Vector embeddings
│       ├── vector_store.py  # Qdrant operations
│       ├── retrieval.py     # Search logic
│       ├── rag_pipeline.py  # RAG orchestration
│       ├── extraction.py    # Structured extraction
│       ├── evaluation.py    # Test harness
│       └── cache.py         # LRU response cache
├── tests/
│   ├── conftest.py          # Shared fixtures
│   └── unit/
│       ├── test_auth.py     # 15 auth tests
│       ├── test_core_services.py  # 21 service tests
│       └── test_evaluation_api.py # 4 evaluation tests
├── scripts/
│   └── run_evaluation.py    # CLI evaluation runner
├── Assets/                  # PDF documents
├── streamlit_app.py         # Demo UI
├── docker-compose.yml       # Service orchestration
├── Dockerfile               # Multi-stage build
└── pyproject.toml           # Dependencies (UV)
```

---

## Configuration

### Environment Variables

```env
# Security
SECRET_KEY=your-secret-key-generate-with-openssl

# LLM Provider
LLM_PROVIDER=ollama              # ollama or openai
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3.2:latest

# OpenAI (if using)
OPENAI_API_KEY=sk-...

# Vector Database
QDRANT_URL=http://qdrant:6333
QDRANT_COLLECTION=constructure_rag

# Test User
TEST_USER_EMAIL=testingcheckuser1234@gmail.com
TEST_USER_PASSWORD=constructure2024
```

### Chunking Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `chunk_size` | 300 words | Optimal for construction docs |
| `chunk_overlap` | 75 words | 25% overlap for context |
| `preserve_tables` | true | Keep table structures intact |
| `page_aware` | true | Track page numbers |

---

## Testing

Built with **TDD methodology** (Red → Green → Refactor):

```bash
# Run all tests
uv run pytest -v

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/unit/test_auth.py -v

# Run fast tests only (skip slow LLM tests)
uv run pytest -v -m "not slow"
```

### Test Statistics
- **40 tests** total
- **~5 seconds** runtime
- **90%+ coverage** on core services

---

## Performance

| Metric | Value | Notes |
|--------|-------|-------|
| PDF Parsing | ~30 pages/sec | PyMuPDF optimized |
| Embedding | ~100 chunks/sec | Batch size 32 |
| Vector Search | <50ms | Qdrant HNSW index |
| LLM Response | 1-3s | Depends on query |
| Cache Hit | <10ms | LRU with 1hr TTL |
| Full E2E Query | 1-4s | Cold/warm cache |

---

## Development

```bash
# Install dependencies
uv sync --all-extras

# Run linter
uv run ruff check src/

# Format code
uv run ruff format src/

# Type checking
uv run mypy src/
```

---

## Docker

```bash
# Build image
docker build -t constructure-backend .

# Run with compose
docker-compose up -d

# View logs
docker-compose logs -f backend

# Shell into container
docker-compose exec backend bash
```

---

## Watermark

All responses, logs, and database entries include:
`CONSTRUCTURE_RAG_VISHAAL_LS_2025`

---

*Built for Constructure AI Technical Assignment | December 2025*
