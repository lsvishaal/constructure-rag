# Project Brain - System Architecture

## High-Level Overview

```mermaid
flowchart TB
    subgraph Client["🖥️ Client Layer"]
        UI[React/Next.js Frontend]
        Demo[Streamlit Demo]
        CLI[CLI Tools]
    end
    
    subgraph API["�� API Gateway"]
        Auth[JWT Authentication]
        Routes[FastAPI Routes]
    end
    
    subgraph Services["⚙️ Core Services"]
        Parser[PDF Parser<br/>PyMuPDF ~30 pg/s]
        Chunker[Smart Chunker<br/>Semantic + Overlap]
        Embeddings[Embedding Service<br/>BGE-small-en-v1.5]
        RAG[RAG Pipeline<br/>+ Caching]
        Extraction[Structured Extractor]
        Eval[Evaluation Harness]
    end
    
    subgraph Storage["💾 Data Layer"]
        Qdrant[(Qdrant Vector DB<br/>384 dimensions)]
        Cache[(LRU Cache<br/>TTL: 1hr)]
    end
    
    subgraph LLM["🧠 AI Layer"]
        Ollama[Ollama Server<br/>llama3.2:1b]
    end
    
    UI --> Auth
    Demo --> Auth
    CLI --> Auth
    Auth --> Routes
    Routes --> Parser
    Routes --> RAG
    Routes --> Extraction
    Routes --> Eval
    Parser --> Chunker
    Chunker --> Embeddings
    Embeddings --> Qdrant
    RAG --> Qdrant
    RAG --> Cache
    RAG --> Ollama
    Extraction --> RAG
    Eval --> RAG
```

---

## Document Ingestion Pipeline

```mermaid
flowchart LR
    subgraph Input
        PDF[📄 PDF Upload]
    end
    
    subgraph Parsing["1️⃣ Parsing"]
        Parser[FastPDFParser<br/>PyMuPDF]
        Meta[Extract Metadata<br/>title, pages, size]
    end
    
    subgraph Chunking["2️⃣ Chunking"]
        Split[Semantic Split<br/>512 chars]
        Overlap[Add Overlap<br/>50 chars]
        Enrich[Add Metadata<br/>page, position]
    end
    
    subgraph Embedding["3️⃣ Embedding"]
        Embed[BGE-small-en-v1.5<br/>384 dimensions]
        Batch[Batch Process<br/>32 chunks]
    end
    
    subgraph Storage["4️⃣ Storage"]
        Qdrant[(Qdrant<br/>Vector Store)]
    end
    
    PDF --> Parser --> Meta --> Split --> Overlap --> Enrich --> Embed --> Batch --> Qdrant
```

---

## RAG Query Pipeline

```mermaid
flowchart TB
    subgraph Query["📝 User Query"]
        Q[Question + Mode]
    end
    
    subgraph Cache["⚡ Cache Layer"]
        Check{Cache Hit?}
        Hit[Return Cached<br/>Response]
    end
    
    subgraph Retrieval["🔍 Retrieval"]
        Embed[Embed Query<br/>BGE-small-en-v1.5]
        Search[Vector Search<br/>Cosine Similarity]
        Rank[Score & Rank<br/>Top-K Results]
    end
    
    subgraph Processing["🧠 Processing"]
        Mode{Mode?}
        QA[QA Mode<br/>Generate Answer]
        Extract[Extraction Mode<br/>Structured Output]
        Sources[Sources Only<br/>No LLM]
    end
    
    subgraph Response["📤 Response"]
        Format[Format Response]
        Store[Cache Result]
        Return[Return to Client]
    end
    
    Q --> Check
    Check -->|Yes| Hit --> Return
    Check -->|No| Embed --> Search --> Rank --> Mode
    Mode -->|qa| QA
    Mode -->|extraction| Extract
    Mode -->|sources_only| Sources
    QA --> Format
    Extract --> Format
    Sources --> Format
    Format --> Store --> Return
```

---

## Authentication Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant A as Auth API
    participant E as Protected Endpoint
    
    C->>A: POST /auth/token<br/>{username, password}
    A->>A: Validate Credentials
    A->>C: {access_token, token_type}
    
    C->>E: GET /chat/modes<br/>Authorization: Bearer {token}
    E->>E: Verify JWT
    E->>C: {modes: [...]}
    
    Note over C,E: Token expires after 30 min
```

---

## Evaluation Harness

```mermaid
flowchart LR
    subgraph Input
        Queries[10 Test Queries<br/>Construction Domain]
    end
    
    subgraph Process
        Loop[For Each Query]
        RAG[RAG Pipeline]
        Score[Calculate Score<br/>0.0 - 1.0]
        Metrics[Collect Metrics<br/>time, sources]
    end
    
    subgraph Output
        Report[Evaluation Report<br/>avg score, latency]
        JSON[JSON Results]
    end
    
    Queries --> Loop --> RAG --> Score --> Metrics --> Report
    Metrics --> JSON
```

---

## Data Models

```mermaid
erDiagram
    DOCUMENT ||--o{ CHUNK : contains
    CHUNK ||--o{ EMBEDDING : has
    
    DOCUMENT {
        string id PK
        string filename
        int pages
        int size_bytes
        datetime uploaded_at
    }
    
    CHUNK {
        string id PK
        string document_id FK
        string content
        int page_number
        int position
        float[] embedding
    }
    
    EMBEDDING {
        string model "BGE-small-en-v1.5"
        int dimensions "384"
        string distance_metric "cosine"
    }
```

---

## API Endpoints

```mermaid
flowchart LR
    subgraph Auth["/auth"]
        Token[POST /token]
    end
    
    subgraph Health["/health"]
        HealthCheck[GET /]
    end
    
    subgraph Docs["/documents"]
        Upload[POST /upload]
        SmartIngest[POST /smart-ingest]
        List[GET /]
        Delete[DELETE /{id}]
    end
    
    subgraph Chat["/chat"]
        Query[POST /]
        Modes[GET /modes]
    end
    
    subgraph Eval["/evaluation"]
        Run[POST /run]
    end
```

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **API** | FastAPI + Pydantic | REST endpoints, validation |
| **Auth** | JWT (python-jose) | Token-based authentication |
| **PDF** | PyMuPDF (fitz) | Fast PDF parsing (~30 pg/s) |
| **Embeddings** | fastembed BGE-small | 384-dim dense vectors |
| **Vector DB** | Qdrant v1.12.1 | Vector storage & search |
| **LLM** | Ollama llama3.2:1b | Local inference |
| **Cache** | Custom LRU + TTL | Response caching |
| **Testing** | pytest | 40 tests, ~4.7s |
| **Demo UI** | Streamlit | Interactive testing |

---

## Performance Characteristics

| Metric | Value | Notes |
|--------|-------|-------|
| PDF Parsing | ~30 pages/sec | PyMuPDF optimized |
| Embedding | ~100 chunks/sec | Batch size 32 |
| Vector Search | <50ms | Qdrant HNSW index |
| LLM Response | 1-3s | Depends on query |
| Cache Hit | <10ms | LRU with 1hr TTL |
| Full Query E2E | 1-4s | Cold / warm |

---

## Deployment Architecture

```mermaid
flowchart TB
    subgraph Vercel["Vercel (Frontend)"]
        Next[Next.js App]
    end
    
    subgraph Backend["Backend Server"]
        FastAPI[FastAPI<br/>:8000]
        Streamlit[Streamlit Demo<br/>:8501]
    end
    
    subgraph Docker["Docker Services"]
        QdrantD[Qdrant<br/>:6333]
        OllamaD[Ollama<br/>:11434]
    end
    
    Next -->|API Calls| FastAPI
    FastAPI --> QdrantD
    FastAPI --> OllamaD
    Streamlit --> FastAPI
```
