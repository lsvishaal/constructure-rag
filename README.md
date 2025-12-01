# 🏗️ Constructure RAG - Full Stack

> Production-grade RAG system for construction document intelligence

A complete document Q&A system built with **FastAPI**, **Next.js**, and **Ollama**. Upload construction PDFs, ask questions in natural language, and receive AI-powered answers with source citations.

---

## 🚀 Quick Start

```bash
# Start everything with one command
make run
```

**Services Available:**
| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Documentation | http://localhost:8000/docs |
| Streamlit UI | http://localhost:8501 |
| Qdrant Dashboard | http://localhost:6333/dashboard |

**Login Credentials:**
```
Email:    testingcheckuser1234@gmail.com
Password: constructure2024
```

---

## 📦 Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Docker & Docker Compose | Latest | Container orchestration |
| Node.js | 18+ | Frontend development |
| Python | 3.12+ | Backend (optional, for local dev) |
| UV | Latest | Python package manager |

---

## ✅ Assignment Requirements

| Part | Requirement | Status | Implementation |
|------|-------------|--------|----------------|
| **0** | Deployment & Testability | ✅ | Docker Compose + Makefile automation |
| **1** | Document Ingestion | ✅ | PyMuPDF @ 30 pages/sec, Qdrant vector storage |
| **2** | RAG Q&A Chat | ✅ | Ollama llama3.2, citations with page references |
| **3** | Structured Extraction | ✅ | Door schedules, wage determination tables |
| **4** | Evaluation Harness | ✅ | 10 test queries, automatic scoring |

### Bonus Features
| Feature | Status | Description |
|---------|--------|-------------|
| Multi-mode Chat | ✅ | `qa`, `extraction`, `sources_only` modes |
| Response Caching | ✅ | LRU cache with 1-hour TTL |
| Streamlit Demo | ✅ | Progress bars for ingestion, interactive chat |
| Next.js Frontend | ✅ | Modern React UI with Framer Motion animations |
| JWT Authentication | ✅ | Secure token-based auth with Argon2 hashing |

---

## 🏛️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     CLIENT LAYER                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  Next.js    │  │  Streamlit  │  │  cURL/API   │              │
│  │  Frontend   │  │   Demo UI   │  │  Testing    │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
└─────────┼────────────────┼────────────────┼─────────────────────┘
          │                │                │
          └────────────────┼────────────────┘
                           │ HTTP/REST + JWT Auth
┌──────────────────────────▼──────────────────────────────────────┐
│                      FASTAPI BACKEND                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │  /auth   │ │  /docs   │ │  /chat   │ │  /eval   │           │
│  │  JWT     │ │  upload  │ │  RAG     │ │  harness │           │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘           │
└───────┼────────────┼────────────┼────────────┼──────────────────┘
        │            │            │            │
┌───────▼────────────▼────────────▼────────────▼──────────────────┐
│                       SERVICE LAYER                              │
│  PDF Parser → Chunker → Embeddings → Vector Store → RAG Pipeline │
│  (PyMuPDF)   (300w)    (BGE-small)   (Qdrant)       (+ Cache)   │
└─────────────────────────────────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                        DATA LAYER                                │
│     ┌───────────────────┐        ┌───────────────────┐          │
│     │      QDRANT       │        │      OLLAMA       │          │
│     │  384-dim vectors  │        │  llama3.2:latest  │          │
│     │  Cosine similarity│        │  Local inference  │          │
│     └───────────────────┘        └───────────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

### Key Technical Decisions

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **Chunking** | 300 words, 75 overlap | Optimal for dense construction specs |
| **Embeddings** | BAAI/bge-small-en-v1.5 | 384 dims, ONNX-based, fast local inference |
| **Vector DB** | Qdrant | Cosine similarity, production-ready |
| **LLM** | Ollama llama3.2 | Local inference, no API costs |
| **Caching** | LRU + TTL | 10x speedup on repeated queries |

---

## 📁 Project Structure

```
constructure-rag/
├── Makefile                 # Build automation
├── backend/
│   ├── docker-compose.yml   # Service orchestration
│   ├── Dockerfile           # Multi-stage build
│   ├── streamlit_app.py     # Demo UI with progress tracking
│   ├── src/
│   │   ├── api/             # FastAPI routes
│   │   ├── core/            # Configuration
│   │   ├── models/          # Pydantic schemas
│   │   └── services/        # Business logic
│   └── tests/               # 40+ tests, TDD-driven
└── frontend/
    ├── app/                 # Next.js 15 App Router
    │   ├── chat/            # Main chat interface
    │   └── login/           # Authentication page
    ├── components/          # React components
    │   ├── chat/            # Chat UI components
    │   ├── extraction/      # Table displays
    │   └── ui/              # shadcn/ui components
    └── lib/                 # Hooks, utilities, API client
```

---

## 🛠️ Make Commands

| Command | Description |
|---------|-------------|
| `make run` | Start all services (backend + frontend) |
| `make run-backend` | Start Docker services only |
| `make run-frontend` | Start Next.js dev server |
| `make down` | Stop all services |
| `make build` | Build containers |
| `make build-clean` | Fresh rebuild (no cache) |
| `make test` | Run backend tests |
| `make logs` | Follow backend logs |
| `make clean-all` | Full reset |

---

## 🔧 Environment Variables

**Backend** (`backend/.env`):
```env
SECRET_KEY=your-secret-key-here
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3.2:latest
QDRANT_URL=http://qdrant:6333
TEST_USER_EMAIL=testingcheckuser1234@gmail.com
TEST_USER_PASSWORD=constructure2024
```

---

## 🔍 API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/login` | POST | OAuth2 login, returns JWT |
| `/api/v1/auth/me` | GET | Current user info |
| `/api/v1/documents` | GET | List indexed documents |
| `/api/v1/documents/upload` | POST | Upload and index PDF |
| `/api/v1/documents/ingest` | POST | Bulk ingest from Assets/ |
| `/api/v1/chat` | POST | RAG query (qa/extraction/sources_only) |
| `/api/v1/evaluation/run` | POST | Run evaluation harness |

---

## 🧪 Testing

Built with **Test-Driven Development** (Red → Green → Refactor):

```bash
# Run all tests
make test

# Run with coverage
cd backend && uv run pytest --cov=src -v

# Run specific test file
cd backend && uv run pytest tests/unit/test_auth.py -v
```

**Test Coverage:** 40 tests across authentication, PDF parsing, chunking, embeddings, RAG pipeline, and evaluation.

---

## 🎯 Development Approach

This project was built using **TDD methodology**:

1. **Red** - Write failing tests first
2. **Green** - Implement minimum code to pass
3. **Refactor** - Optimize while keeping tests green

Key development phases:
- Phase 1: PDF parsing & chunking (PyMuPDF, 30 pages/sec)
- Phase 2: Embeddings & vector storage (Qdrant)
- Phase 3: RAG pipeline with caching
- Phase 4: Structured extraction (door schedules, wage tables)
- Phase 5: Evaluation harness (10 queries, auto-scoring)
- Phase 6: Frontend (Next.js 15 + Framer Motion)

---

## 📚 Documentation

| Document | Location | Description |
|----------|----------|-------------|
| Backend README | `backend/README.md` | Detailed backend documentation |
| Frontend README | `frontend/README.md` | Frontend architecture & setup |
| Architecture | `backend/docs/ARCHITECTURE.md` | System design diagrams |
| Testing Guide | `backend/docs/TESTING_GUIDE.md` | Manual testing procedures |

---

## 📝 Watermark

`CONSTRUCTURE_RAG_VISHAAL_LS_2025`

---

*Built for Constructure AI Technical Assignment | December 2025*
