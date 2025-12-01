# QUICK START: 36-HOUR RAG ASSIGNMENT

## TL;DR TIMELINE

**Hour 0-12 (Day 1):**
- 1h: Project setup (UV, Docker, FastAPI boilerplate)
- 2h: Write + implement PDF parser tests (TDD)
- 2h: Write + implement chunking tests (3 strategies)
- 2h: Benchmark chunking performance
- 2h: Integrate watermark everywhere
- 2h: First GitHub commit, verify tests passing

**Hour 12-24 (Day 2):**
- 1h: Embedding tests (OpenAI API)
- 2h: OpenAI embedder implementation
- 2h: Qdrant vector store tests
- 2h: Qdrant implementation
- 2h: Performance benchmarking
- 2h: Add Prometheus metrics
- 1h: GitHub commit

**Hour 24-36 (Day 3):**
- 2h: Retrieval tests (hybrid search)
- 2h: Retrieval implementation
- 2h: LLM orchestration tests
- 2h: Structured extraction tests + implementation
- 2h: Evaluation harness (5-10 test queries)
- 2h: Record video demo + GitHub release
- 2h: Final README + setup docs

---

## CRITICAL COMMANDS

```bash
# ONE-TIME SETUP
git init
uv venv
source .venv/bin/activate

# EVERY PHASE
# 1. Write tests
cat > tests/test_XXX.py << 'EOF'
# TDD tests here
EOF

# 2. Implement code
cat > src/XXX.py << 'EOF'
# Implementation with watermark
EOF

# 3. Run + verify
uv run pytest tests/test_XXX.py -v
uv run ruff check src/XXX.py
uv run ruff format src/

# 4. Commit
git add tests/test_XXX.py src/XXX.py
git commit -m "Phase X: XXX - Tests passing, performance benchmarked"

# FINAL
docker-compose up  # Verify everything works
python scripts/verify_watermark.py  # Prove watermark is integrated
```

---

## WATERMARK: ONE-LINE EVERYWHERE

```python
# config.py
PROJECT_ID = "CONSTRUCTURE_RAG_VISHAAL_LS_2025"
WATERMARK = "constructed-by-vishaal-LS"

# In every class/function
class MyClass:
    watermark = WATERMARK  # ← HERE
    
    def process(self):
        logger.info(f"[{PROJECT_ID}] Processing...")  # ← HERE
        return {"data": ..., "watermark": WATERMARK}  # ← HERE

# In database
{"text": "...", "watermark": WATERMARK}  # ← HERE

# In API response
response.headers["X-Watermark"] = WATERMARK  # ← HERE
```

---

## PHASES CHECKLIST

### Phase 1: PDF + Chunking ✓
- [ ] `tests/test_pdf_parser.py` passing
- [ ] `tests/test_chunking_strategy.py` passing
- [ ] Performance: <100ms to chunk 10 pages
- [ ] Watermark in every chunk
- [ ] Commit #1

### Phase 2: Embeddings + Vector Store ✓
- [ ] `tests/test_embedding.py` passing
- [ ] `tests/test_vector_store.py` passing
- [ ] Performance: embedding <100ms, search <50ms
- [ ] Qdrant running in Docker
- [ ] Watermark in every vector payload
- [ ] Commit #2

### Phase 3: Retrieval ✓
- [ ] `tests/test_retrieval.py` passing
- [ ] Hybrid search (vector + keyword)
- [ ] Performance: <200ms p95
- [ ] Commit #3

### Phase 4: RAG Pipeline ✓
- [ ] `tests/test_rag_pipeline.py` passing
- [ ] Full Q&A working
- [ ] Sources cited correctly
- [ ] Performance: <3s p95 end-to-end
- [ ] Commit #4

### Phase 5: Extraction ✓
- [ ] `tests/test_extraction.py` passing
- [ ] Door schedule JSON working
- [ ] Accuracy >90%
- [ ] Commit #5

### Phase 6: Evaluation ✓
- [ ] `scripts/run_evaluation.py` passes 10 queries
- [ ] Prometheus metrics showing
- [ ] Grafana dashboard displaying
- [ ] Commit #6

---

## PERFORMANCE TARGETS (Must Hit)

| Component | Target | Status |
|-----------|--------|--------|
| PDF parsing | <100ms per page | ? |
| Chunking | <50ms per 1000 tokens | ? |
| Embedding | <100ms per text | ? |
| Search | <50ms p95 | ? |
| LLM call | <3s p95 | ? |
| Full RAG | <5s p95 end-to-end | ? |

---

## FREE HOSTING SOLUTION

**You can't use free tiers (Vercel, Railway timeout). Instead:**

1. **Record 5-min video demo**
   - Upload to PDF
   - Ask questions
   - Show sources
   - Show structured extraction

2. **Push code to GitHub**
   ```bash
   git remote add origin https://github.com/USERNAME/constructure-rag
   git branch -M main
   git push -u origin main
   ```

3. **Create release with video**
   ```bash
   gh release create v1.0 \
     -t "Constructure RAG Assignment" \
     -n "See video demo in assets. Run locally: docker-compose up" \
     demo.mp4
   ```

4. **Vercel for frontend only** (no backend calls)
   - Or just include screenshot in README

5. **Instructions: docker-compose up works locally**

---

## WATERMARK PROOF

```bash
# Run to show watermark is integrated
python scripts/verify_watermark.py

# Output:
# Found 47 watermark references across 12 files
# Removing watermark = code breaks immediately
# ✓ Watermark cannot be removed without rewriting entire project
```

---

## SUBMIT WITH

- [ ] GitHub repo (public, all tests passing)
- [ ] README.md (clear setup instructions)
- [ ] demo_video.mp4 (GitHub release asset, 5 min)
- [ ] performance_metrics.txt (benchmark results)
- [ ] watermark_verification.txt (proof of integration)
- [ ] docker-compose.yml (works with `docker-compose up`)

---

## REALITY CHECK: 36 HOURS IS TIGHT

Don't over-engineer:
- ❌ Fancy UI (basic chat is fine)
- ❌ Multiple LLM providers (one is enough)
- ❌ Production database (in-memory is fine)
- ✅ Working functionality
- ✅ Tests passing
- ✅ Performance metrics
- ✅ Watermark integrated
- ✅ Video demo working

Focus on: **Shipping a working MVP, not perfection**

---

## GIT STRATEGY

```bash
# Commit frequently (every phase)
git add tests/ src/
git commit -m "Phase 1: PDF parsing + chunking - All tests passing, p95 <100ms"

# This shows:
# - You're TDD-first
# - You ship incrementally
# - Tests prove it works
# - Each commit is a milestone
```

---

## IF YOU GET STUCK

**PDF parsing**: Use `pdfplumber` (handles 95% of PDFs)
**Embedding**: Use `openai.embeddings` (most reliable)
**Vector DB**: Use `Qdrant` (easiest to deploy)
**LLM**: Use `gpt-3.5-turbo` (fast + cheap)
**Frontend**: Use `Next.js App Router` (modern + simple)
**Deployment**: Use `video demo + docker-compose`

---

## SUBMIT TIME

- [ ] Code pushed to GitHub
- [ ] Tests all passing (`pytest tests/ -v`)
- [ ] Video demo uploaded (GitHub release)
- [ ] README has setup instructions
- [ ] Performance metrics documented
- [ ] Watermark verification script passing
- [ ] `docker-compose up` works locally

**You're done. Ship it.**
