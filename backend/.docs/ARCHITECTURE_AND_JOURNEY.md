# Project Brain - Architecture & Development Journey

> A comprehensive document detailing every architectural decision, challenge conquered, and lesson learned during the development of this RAG system.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture Deep Dive](#architecture-deep-dive)
3. [Development Journey](#development-journey)
4. [Technical Decisions](#technical-decisions)
5. [Challenges & Solutions](#challenges--solutions)
6. [Performance Optimizations](#performance-optimizations)
7. [What We Built](#what-we-built)
8. [Lessons Learned](#lessons-learned)

---

## Project Overview

### The Mission
Build a "Project Brain" for construction documents - a RAG system that can:
- Ingest construction PDFs (drawings, wage determinations)
- Answer natural language questions with source citations
- Extract structured data (schedules, tables)
- Evaluate its own accuracy

### The Constraints
- **36-hour deadline**
- **Tech stack:** FastAPI backend, React/Next.js frontend
- **Must work:** Not a notebook demo, a real deployable app
- **Test user:** `testingcheckuser1234@gmail.com`

### The Approach
**TDD-first development** - Every feature started with a failing test, then implementation, then refactor. This ensured quality and prevented regressions throughout the rapid development cycle.

---

## Architecture Deep Dive

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  React UI   │  │  Streamlit  │  │  cURL/API   │              │
│  │  (pending)  │  │   (demo)    │  │  (testing)  │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
└─────────┼────────────────┼────────────────┼─────────────────────┘
          │                │                │
          └────────────────┼────────────────┘
                           │ HTTP/REST
┌──────────────────────────▼──────────────────────────────────────┐
│                      FASTAPI BACKEND                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │  /auth   │ │  /docs   │ │  /chat   │ │  /eval   │           │
│  │  JWT+    │ │  upload  │ │  RAG     │ │  test    │           │
│  │  Argon2  │ │  ingest  │ │  query   │ │  harness │           │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘           │
└───────┼────────────┼────────────┼────────────┼──────────────────┘
        │            │            │            │
┌───────▼────────────▼────────────▼────────────▼──────────────────┐
│                       SERVICE LAYER                              │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   INGESTION PIPELINE                     │    │
│  │  PDF ──► FastParser ──► Chunker ──► Embeddings ──► Store │    │
│  │       (PyMuPDF)    (400+50)   (BGE-small)    (Qdrant)   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    QUERY PIPELINE                        │    │
│  │  Query ──► Cache? ──► Retrieval ──► RAG ──► LLM ──► Ans │    │
│  │              │         (vector)   (prompt)  (Ollama)     │    │
│  │              ▼                                           │    │
│  │         CacheService (LRU + TTL)                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                  EXTRACTION PIPELINE                     │    │
│  │  Query ──► Detect Type ──► Retrieve ──► Parse ──► JSON  │    │
│  │         (door/wage/etc)                  (regex+LLM)     │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                        DATA LAYER                                │
│  ┌───────────────────┐        ┌───────────────────┐             │
│  │      QDRANT       │        │      OLLAMA       │             │
│  │  ┌─────────────┐  │        │  ┌─────────────┐  │             │
│  │  │ Vectors     │  │        │  │ llama3.2:1b │  │             │
│  │  │ 384 dims    │  │        │  │ ~1.3GB      │  │             │
│  │  │ Cosine sim  │  │        │  │ Local       │  │             │
│  │  └─────────────┘  │        │  └─────────────┘  │             │
│  │  Port: 6333       │        │  Port: 11434      │             │
│  └───────────────────┘        └───────────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
INGESTION:
┌──────┐    ┌───────────┐    ┌─────────┐    ┌──────────┐    ┌────────┐
│ PDF  │───►│ FastParser│───►│ Chunker │───►│Embeddings│───►│ Qdrant │
│ file │    │ (PyMuPDF) │    │(400+50) │    │(BGE-small│    │(vector)│
└──────┘    └───────────┘    └─────────┘    └──────────┘    └────────┘
              30 pg/s        page-aware      384 dims       indexed

QUERY:
┌───────┐   ┌───────┐   ┌──────────┐   ┌─────┐   ┌────────┐   ┌────────┐
│ User  │──►│ Cache │──►│ Retrieval│──►│ RAG │──►│ Ollama │──►│Response│
│ Query │   │  LRU  │   │  top-5   │   │prompt│  │  LLM   │   │+sources│
└───────┘   └───────┘   └──────────┘   └─────┘   └────────┘   └────────┘
             1hr TTL     cosine sim    concise    llama3.2:1b  citations
```

---

## Development Journey

### Phase 1: Foundation (TDD Setup)
**Goal:** Establish testing infrastructure before any features

**What we did:**
1. Set up pytest with proper fixtures
2. Created module-scoped embedding fixture (expensive operation, load once)
3. Established in-memory vector store for fast tests
4. Configured watermarking for attribution

**Key insight:** Spending 30 minutes on test infrastructure saved hours later. Tests run in ~5 seconds, enabling rapid iteration.

### Phase 2: Core Services
**Goal:** Build the ingestion pipeline

**Evolution of PDF parsing:**
1. Started with `pdfplumber` - functional but SLOW (4+ minutes for 68 pages)
2. Tried `pdfminer.six` - marginal improvement
3. Landed on `PyMuPDF (fitz)` - **2.3 seconds for 68 pages** (100x faster!)

**Chunking strategy decisions:**
- Tested 200, 400, 600, 800 char chunks
- 400 chars optimal for construction docs (dense technical info)
- 50 char overlap preserves context across boundaries
- Page-boundary aware (never split mid-page for citations)

### Phase 3: RAG Pipeline
**Goal:** Answer questions with sources

**Retrieval approach:**
- Pure vector search initially
- Added keyword search capability (not always used)
- Cosine similarity with top-5 retrieval
- Metadata preserved for citations

**LLM integration:**
- Ollama for local development (no API costs)
- OpenAI fallback for production
- Mock provider for fast tests

**Prompt engineering:**
- Started verbose → got slow, rambling responses
- Optimized to: "Be concise. Cite [Page X]."
- Added temperature=0.3 for focused outputs
- Limited to 200 tokens max

### Phase 4: Structured Extraction
**Goal:** Extract door schedules, wage tables

**Approach:**
- Regex for well-formatted data
- LLM fallback for messy extraction
- Type detection from query keywords

**Schema design:**
```json
{
  "mark": "D-101",
  "location": "Level 1 Corridor",
  "width_mm": 900,
  "height_mm": 2100,
  "fire_rating": "1 HR",
  "material": "Hollow Metal"
}
```

### Phase 5: Evaluation Harness
**Goal:** Measure quality automatically

**Test queries created:**
1. Wage rate questions (plumber: $39.13)
2. Fringe benefits (electrician: $20.04)
3. Project identification (508-22-105)
4. Edge cases (weather forecast → should fail gracefully)

**Scoring logic:**
- **Correct:** All expected keywords found
- **Partial:** Some keywords found
- **Wrong:** No keywords or hallucination

### Phase 6: Polish & Caching
**Goal:** Performance and reliability

**Caching implementation:**
- LRU eviction (1000 entry max)
- 1-hour TTL
- Cache key = hash(query + top_k + model)
- ~10x speedup on repeated queries

---

## Technical Decisions

### Why PyMuPDF over pdfplumber?

| Aspect | pdfplumber | PyMuPDF |
|--------|------------|---------|
| 68-page PDF | 4+ minutes | 2.3 seconds |
| Memory | Higher | Lower |
| Text quality | Good | Good |
| Table extraction | Better | Adequate |

**Decision:** Speed trumps marginally better tables for this use case.

### Why BGE-small-en-v1.5?

| Model | Dimensions | Speed | Quality |
|-------|------------|-------|---------|
| OpenAI ada-002 | 1536 | Fast (API) | Excellent |
| BGE-small | 384 | Fast (local) | Very good |
| all-MiniLM | 384 | Fast (local) | Good |

**Decision:** Local inference, no API dependency, good enough quality.

### Why 400-char chunks?

Tested on construction documents:
- 200 chars: Too fragmented, lost context
- 400 chars: Sweet spot, coherent units
- 800 chars: Often mixed topics, hurt retrieval

### Why Ollama llama3.2:1b?

| Model | Size | Speed | Quality |
|-------|------|-------|---------|
| llama3.2:1b | 1.3GB | Fast (CPU) | Good |
| llama3.2:3b | 2GB | Slower | Better |
| llama3.1:8b | 4.7GB | Slow | Best |

**Decision:** 1b model gives acceptable answers in 10-30 seconds on CPU. Production would use larger model or OpenAI.

---

## Challenges & Solutions

### Challenge 1: PDF Parsing Speed
**Problem:** pdfplumber took 4+ minutes for 68-page construction drawings
**Impact:** Development iteration was painfully slow
**Solution:** Switched to PyMuPDF, achieved 30 pages/second
**Lesson:** Always benchmark libraries before committing

### Challenge 2: LLM Response Time
**Problem:** Initial Ollama responses took 2-3 minutes
**Root cause:** Default model (llama3.2:3b) + verbose prompts + high token limits
**Solution:**
1. Switched to 1b model
2. Reduced prompt to essential instructions
3. Limited output to 200 tokens
4. Added caching
**Result:** 10-30 second responses, instant on cache hit

### Challenge 3: Citation Accuracy
**Problem:** LLM would cite wrong pages or make up sources
**Solution:**
1. Pass explicit [Page X] markers in context
2. Prompt: "Cite ONLY from provided context"
3. Post-process to validate citations exist
**Result:** Citations now match actual source pages

### Challenge 4: Test Performance
**Problem:** Tests were slow (30+ seconds) due to embedding model loading
**Solution:** Module-scoped fixture loads model once per test file
**Result:** 40 tests in ~5 seconds

### Challenge 5: Multiple Parser Files
**Problem:** Accumulated 4 different parser implementations during experimentation
**Solution:** Kept only the performant ones:
- `fast_parser.py` (production)
- `pdf_parser.py` (fallback)
**Lesson:** Clean up experimental code before it becomes tech debt

---

## Performance Optimizations

### Ingestion Performance
| Optimization | Before | After | Improvement |
|--------------|--------|-------|-------------|
| PDF parsing | 4 min | 2.3 sec | 100x |
| Batch embedding | Serial | Batch | 3x |
| Chunk size tuning | N/A | 400 chars | Better retrieval |

### Query Performance
| Optimization | Before | After | Improvement |
|--------------|--------|-------|-------------|
| LLM model | 3b | 1b | 3x faster |
| Token limit | 500 | 200 | 2x faster |
| Caching | None | LRU+TTL | 10x on hit |
| Prompt length | Verbose | Concise | 2x faster |

### Test Performance
| Optimization | Before | After | Improvement |
|--------------|--------|-------|-------------|
| Embedding fixture | Per-test | Per-module | 6x |
| Vector store | Real Qdrant | In-memory | 3x |
| Test count | 76 scattered | 40 focused | 2x |

---

## What We Built

### Services Implemented (11 modules)

1. **auth.py** - JWT authentication with Argon2 hashing
2. **fast_parser.py** - PyMuPDF-based PDF extraction
3. **chunking.py** - Page-aware text splitting
4. **embeddings.py** - BGE-small vector generation
5. **vector_store.py** - Qdrant integration
6. **retrieval.py** - Vector + keyword search
7. **rag_pipeline.py** - Complete RAG with caching
8. **extraction.py** - Structured data output
9. **evaluation.py** - Test harness with scoring
10. **cache.py** - LRU response cache
11. **pdf_parser.py** - Fallback parser

### API Endpoints (14 total)

**Auth (3):** token, me, verify
**Documents (5):** list, upload, ingest, smart-ingest, clear
**Chat (1):** query with 3 modes
**Evaluation (3):** queries, run, score
**Health (2):** health, root

### Tests (40 total)

- Auth service: 9 tests
- Auth API: 6 tests
- PDF parsing: 2 tests
- Chunking: 1 test
- Embeddings: 2 tests
- Vector store: 2 tests
- Retrieval: 1 test
- RAG pipeline: 1 test
- Extraction: 3 tests
- Evaluation: 4 tests
- Caching: 5 tests
- Evaluation API: 4 tests

---

## Lessons Learned

### 1. TDD Pays Off Exponentially
Writing tests first seemed slow initially but prevented countless bugs and made refactoring fearless.

### 2. Benchmark Before Committing
The PDF parser decision would have been obvious if we'd benchmarked first. "Works" isn't the same as "works well."

### 3. Start Simple, Optimize Later
Initial RAG worked with verbose prompts. Optimization came after we had working features.

### 4. Local LLM Development is Viable
Ollama + small models enabled rapid iteration without API costs. Switch to OpenAI for production quality.

### 5. Cache Everything Expensive
LLM calls are slow. Caching identical queries gave us "instant" responses for repeated questions.

### 6. Construction Documents are Dense
Standard web chunking (1000+ chars) doesn't work. Dense technical docs need smaller chunks (400 chars).

### 7. Watermarking is Non-Negotiable
Every response, log, and database entry has our watermark. Makes debugging and attribution trivial.

---

## Appendix: File Structure

```
backend/
├── src/
│   ├── api/
│   │   ├── auth.py          # JWT endpoints
│   │   ├── chat.py          # RAG query endpoint
│   │   ├── documents.py     # Ingestion endpoints
│   │   ├── evaluation.py    # Test harness endpoints
│   │   └── health.py        # Health checks
│   ├── core/
│   │   └── config.py        # Settings + watermarks
│   ├── models/
│   │   ├── auth.py          # User, Token models
│   │   ├── chat.py          # ChatRequest, ChatResponse
│   │   ├── documents.py     # Document models
│   │   └── extraction.py    # Extraction schemas
│   └── services/
│       ├── auth.py          # Auth logic
│       ├── fast_parser.py   # PyMuPDF parser
│       ├── pdf_parser.py    # Fallback parser
│       ├── chunking.py      # Text chunking
│       ├── embeddings.py    # Vector generation
│       ├── vector_store.py  # Qdrant ops
│       ├── retrieval.py     # Search logic
│       ├── rag_pipeline.py  # RAG + cache
│       ├── extraction.py    # Structured output
│       ├── evaluation.py    # Test harness
│       └── cache.py         # LRU cache
├── tests/
│   ├── conftest.py          # Shared fixtures
│   └── unit/
│       ├── test_auth.py
│       ├── test_core_services.py
│       └── test_evaluation_api.py
├── scripts/
│   └── run_evaluation.py    # CLI evaluator
├── Assets/                   # PDF documents
├── streamlit_app.py         # Demo UI
├── docker-compose.yml       # Services
├── pyproject.toml           # Dependencies
└── .env.example             # Config template
```

---

*Document Version: 1.0*
*Last Updated: December 2024*
*Project: Constructure AI Technical Assignment*
*Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025*
