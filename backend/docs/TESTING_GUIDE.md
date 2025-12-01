# Project Brain - Manual Testing Guide

> Complete guide for manually testing all features of the RAG system

## Prerequisites

### 1. Start Required Services

```bash
# Terminal 1: Qdrant Vector Database
docker run -d --name qdrant -p 6333:6333 qdrant/qdrant:v1.12.1

# Terminal 2: Ollama LLM
ollama serve  # Then: ollama pull llama3.2:1b

# Terminal 3: FastAPI Backend
cd backend && uvicorn src.main:app --reload --port 8000
```

### 2. Verify Services Health

```bash
# Check all services
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "services": {
    "qdrant": "healthy",
    "ollama": "healthy"
  }
}
```

---

## Test 1: Authentication

### 1.1 Get API Token

```bash
# Login to get JWT token
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=secret"

# Save the token
export TOKEN="<paste_access_token_here>"
```

### 1.2 Test Protected Endpoint

```bash
# This should work
curl http://localhost:8000/chat/modes \
  -H "Authorization: Bearer $TOKEN"

# This should fail (401)
curl http://localhost:8000/chat/modes
```

---

## Test 2: Document Ingestion

### 2.1 Upload a PDF Document

```bash
# Upload construction document
curl -X POST http://localhost:8000/documents/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@your_document.pdf"

# Expected: {"document_id": "...", "chunks_stored": 150, ...}
```

### 2.2 Smart Ingest (Structured)

```bash
# Upload with smart parsing
curl -X POST http://localhost:8000/documents/smart-ingest \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@your_document.pdf"

# Expected: Returns document with sections and subsections
```

### 2.3 List Documents

```bash
curl http://localhost:8000/documents/ \
  -H "Authorization: Bearer $TOKEN"
```

### 2.4 Delete a Document

```bash
curl -X DELETE http://localhost:8000/documents/{document_id} \
  -H "Authorization: Bearer $TOKEN"
```

---

## Test 3: RAG Q&A

### 3.1 Basic Question

```bash
curl -X POST http://localhost:8000/chat/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the concrete specifications?",
    "mode": "qa"
  }'
```

### 3.2 Sources-Only Mode

```bash
curl -X POST http://localhost:8000/chat/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "rebar requirements",
    "mode": "sources_only"
  }'

# Returns only retrieved chunks, no LLM processing
```

### 3.3 Test Caching

```bash
# Run same query twice
time curl -X POST http://localhost:8000/chat/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the project scope?"}'

# Second call should be faster (cached)
time curl -X POST http://localhost:8000/chat/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the project scope?"}'
```

---

## Test 4: Structured Data Extraction

### 4.1 Extract Project Metadata

```bash
curl -X POST http://localhost:8000/chat/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Extract project name, location, and owner",
    "mode": "extraction"
  }'
```

### 4.2 Extract Materials List

```bash
curl -X POST http://localhost:8000/chat/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "List all concrete specifications with psi values",
    "mode": "extraction"
  }'
```

---

## Test 5: Evaluation Harness

### 5.1 Run Evaluation via API

```bash
curl -X POST http://localhost:8000/evaluation/run \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"queries": ["What are the concrete requirements?", "Describe the site conditions"]}'
```

### 5.2 Run Full Evaluation via CLI

```bash
cd backend
python -m src.cli.evaluate --top-k 5 --verbose

# Sample output:
# ================================================================================
# Project Brain Evaluation Harness
# ================================================================================
# 
# [1/10] What are the concrete strength requirements for foundations?
#        Score: 0.85 | Sources: 5 | Time: 1.23s
# ...
# ================================================================================
# SUMMARY
# ================================================================================
# Average Score: 0.75
# Average Retrieval Time: 0.45s
```

---

## Test 6: Streamlit Demo UI

### 6.1 Launch Demo

```bash
cd backend
streamlit run streamlit_app.py
# Opens at http://localhost:8501
```

### 6.2 Demo Features to Test

1. **📄 Upload PDF** - Sidebar upload widget
2. **📊 View Stats** - Document and chunk counts
3. **💬 Ask Questions** - Main chat interface
4. **🔍 Mode Selection** - QA / Extraction / Sources Only
5. **📋 View Sources** - Expandable source citations

---

## Test 7: Error Handling

### 7.1 Invalid File Type

```bash
curl -X POST http://localhost:8000/documents/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@image.png"

# Expected: 400 Bad Request
```

### 7.2 Empty Query

```bash
curl -X POST http://localhost:8000/chat/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": ""}'

# Expected: Validation error
```

### 7.3 No Documents

```bash
# With empty vector store
curl -X POST http://localhost:8000/chat/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "test query"}'

# Expected: Empty sources array
```

---

## Test 8: Performance Benchmarks

### 8.1 Document Ingestion Speed

```bash
# Upload large PDF (100+ pages)
time curl -X POST http://localhost:8000/documents/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@large_spec.pdf"

# Target: ~30 pages/second
```

### 8.2 Query Latency

```bash
# Measure end-to-end query time
for i in {1..10}; do
  time curl -s -X POST http://localhost:8000/chat/ \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"question": "What are the safety requirements?"}' > /dev/null
done

# Target: < 3 seconds average
```

---

## Automated Test Suite

```bash
# Run all unit tests
cd backend && pytest -v

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_rag_pipeline.py -v
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Qdrant connection failed | `docker start qdrant` |
| Ollama not responding | `ollama serve` then `ollama pull llama3.2:1b` |
| Empty retrieval results | Upload documents first |
| Slow responses | Check Ollama GPU/CPU mode |
| 401 Unauthorized | Re-authenticate for new token |

---

## Quick Health Check Script

```bash
#!/bin/bash
echo "=== Project Brain Health Check ==="
echo ""
echo "1. Qdrant:" && curl -s http://localhost:6333/health | head -1
echo "2. Ollama:" && curl -s http://localhost:11434/api/tags | head -1  
echo "3. Backend:" && curl -s http://localhost:8000/health | jq -r '.status'
echo ""
echo "✅ All services operational!"
```

---

*Last updated: $(date +%Y-%m-%d)*
