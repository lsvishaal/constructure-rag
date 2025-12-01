"""
Streamlit Demo UI for Constructure RAG.

Upload PDFs, ingest them, and chat with the RAG system.

Run: uv run streamlit run streamlit_app.py

Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
"""
import os
import sys
import time
import tempfile
import logging
from pathlib import Path

import streamlit as st
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="Constructure RAG Demo",
    page_icon="🏗️",
    layout="wide",
)

# =============================================================================
# Configuration
# =============================================================================

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
TEST_EMAIL = "testingcheckuser1234@gmail.com"
TEST_PASSWORD = "constructure2024"


# =============================================================================
# Session State Init
# =============================================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "token" not in st.session_state:
    st.session_state.token = None

if "indexed_docs" not in st.session_state:
    st.session_state.indexed_docs = []

if "ingestion_stats" not in st.session_state:
    st.session_state.ingestion_stats = None


# =============================================================================
# API Functions
# =============================================================================

def login() -> str | None:
    """Login and get JWT token."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/auth/login",
            data={"username": TEST_EMAIL, "password": TEST_PASSWORD},
            timeout=10,
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            st.error(f"Login failed: {response.text}")
            return None
    except Exception as e:
        st.error(f"Connection error: {e}")
        return None


def get_auth_headers() -> dict:
    """Get authorization headers."""
    if not st.session_state.token:
        st.session_state.token = login()
    return {"Authorization": f"Bearer {st.session_state.token}"}


def chat_query(query: str, mode: str = "qa") -> dict | None:
    """Send chat query to RAG API."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/chat",
            headers=get_auth_headers(),
            json={"query": query, "mode": mode, "top_k": 5},
            timeout=120,
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Chat error: {response.text}")
            return None
    except Exception as e:
        st.error(f"Chat error: {e}")
        return None


def ingest_documents() -> dict | None:
    """Trigger document ingestion via API."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/documents/ingest",
            headers=get_auth_headers(),
            timeout=300,  # 5 min timeout for large PDFs
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Ingestion error: {response.text}")
            return None
    except Exception as e:
        st.error(f"Ingestion error: {e}")
        return None


def get_document_stats() -> dict | None:
    """Get current document stats."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/documents",
            headers=get_auth_headers(),
            timeout=10,
        )
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except:
        return None


# =============================================================================
# Local Processing (for demo without API)
# =============================================================================

@st.cache_resource
def get_local_services():
    """Initialize local services (cached)."""
    from src.services.fast_parser import FastPDFParser
    from src.services.chunking import ChunkingService
    from src.services.embeddings import EmbeddingService
    from src.services.vector_store import VectorStoreService
    from src.services.retrieval import RetrievalService
    from src.services.rag_pipeline import RAGPipeline
    from src.core.config import settings
    
    # Initialize base services
    embeddings = EmbeddingService()
    vector_store = VectorStoreService(
        url=settings.qdrant_url,
        collection_name=settings.qdrant_collection,
        use_memory=False,
    )
    
    # Create retrieval service (needed by RAG)
    retrieval = RetrievalService(
        embedding_service=embeddings,
        vector_store=vector_store,
    )
    
    # Create RAG pipeline with retrieval service
    rag = RAGPipeline(
        retrieval_service=retrieval,
        llm_provider=settings.llm_provider,  # 'ollama' or 'openai'
        ollama_url=settings.ollama_base_url,
        ollama_model=settings.ollama_model,
    )
    
    return {
        "parser": FastPDFParser(),
        "chunker": ChunkingService(chunk_size=400, chunk_overlap=50),
        "embeddings": embeddings,
        "vector_store": vector_store,
        "retrieval": retrieval,
        "rag": rag,
    }


def process_uploaded_pdf(uploaded_file, progress_bar, status_text):
    """Process uploaded PDF locally with progress."""
    services = get_local_services()
    parser = services["parser"]
    chunker = services["chunker"]
    embeddings = services["embeddings"]
    vector_store = services["vector_store"]
    
    # Save uploaded file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.getvalue())
        tmp_path = tmp.name
    
    try:
        # Step 1: Parse PDF
        status_text.text("📄 Step 1/3: Parsing PDF...")
        
        def on_progress(p):
            progress_bar.progress(
                int(p.percent * 0.33),  # First 33% for parsing
                text=f"Parsing page {p.current_page}/{p.total_pages} ({p.pages_per_second:.0f} pg/s)"
            )
        
        result = parser.parse(tmp_path, on_progress=on_progress)
        
        # Step 2: Chunk
        status_text.text("✂️ Step 2/3: Chunking text...")
        progress_bar.progress(40, text="Creating chunks...")
        
        chunks = []
        for page in result.pages:
            if page.has_text:
                page_chunks = chunker.chunk(
                    text=page.text,
                    source_file=uploaded_file.name,
                    page=page.page_number,
                )
                chunks.extend(page_chunks)
        
        # Step 3: Embed and store
        status_text.text("🔢 Step 3/3: Embedding and indexing...")
        
        from src.services.embeddings import EmbeddedChunk
        
        for i, chunk in enumerate(chunks):
            progress = 50 + int((i / len(chunks)) * 50)  # 50-100%
            progress_bar.progress(
                progress,
                text=f"Indexing chunk {i+1}/{len(chunks)}"
            )
            
            vector = embeddings.embed(chunk.text)
            embedded = EmbeddedChunk(
                text=chunk.text,
                vector=vector,
                metadata={
                    "source_file": chunk.source_file,
                    "page": chunk.page,
                    "chunk_index": chunk.chunk_index,
                },
                watermark="CONSTRUCTURE_RAG_VISHAAL_LS_2025",
            )
            vector_store.store(embedded)
        
        progress_bar.progress(100, text="✅ Complete!")
        
        return {
            "file_name": uploaded_file.name,
            "total_pages": result.total_pages,
            "text_pages": result.text_pages,
            "chunks": len(chunks),
            "parse_time": result.elapsed_seconds,
        }
        
    finally:
        os.unlink(tmp_path)


def local_chat_query(query: str, mode: str = "qa") -> dict:
    """Run RAG query locally."""
    services = get_local_services()
    rag = services["rag"]
    
    # Query - note: RAGPipeline.query doesn't have 'mode' param, just top_k
    result = rag.query(query, top_k=5)
    
    return {
        "answer": result.answer,
        "sources": [
            {
                "source_file": c.source_file,
                "page": c.page,
                "text": c.text[:200] + "..." if len(c.text) > 200 else c.text,
                "score": c.score,
            }
            for c in result.citations
        ],
        "mode": mode,
    }


# =============================================================================
# UI Components
# =============================================================================

st.title("🏗️ Constructure RAG Demo")
st.caption("Upload construction documents and chat with them using AI")

# Sidebar
with st.sidebar:
    st.header("📤 Document Upload")
    
    uploaded_file = st.file_uploader(
        "Upload PDF",
        type=["pdf"],
        help="Upload a construction document PDF"
    )
    
    if uploaded_file:
        if st.button("🚀 Process Document", type="primary"):
            progress_bar = st.progress(0, text="Starting...")
            status_text = st.empty()
            
            with st.spinner("Processing..."):
                try:
                    stats = process_uploaded_pdf(uploaded_file, progress_bar, status_text)
                    st.session_state.ingestion_stats = stats
                    st.session_state.indexed_docs.append(stats["file_name"])
                    st.success(f"✅ Indexed {stats['chunks']} chunks from {stats['total_pages']} pages!")
                except Exception as e:
                    st.error(f"Error: {e}")
                    logger.exception("Processing error")
    
    st.divider()
    
    # Stats
    st.header("📊 Index Stats")
    if st.session_state.ingestion_stats:
        stats = st.session_state.ingestion_stats
        st.metric("Pages", stats.get("total_pages", 0))
        st.metric("Chunks", stats.get("chunks", 0))
        st.metric("Parse Time", f"{stats.get('parse_time', 0):.1f}s")
    
    if st.session_state.indexed_docs:
        st.write("**Indexed Documents:**")
        for doc in st.session_state.indexed_docs:
            st.write(f"• {doc}")
    
    st.divider()
    
    # Mode selector
    st.header("⚙️ Chat Mode")
    mode = st.selectbox(
        "Query Mode",
        options=["qa", "extraction", "sources_only"],
        format_func=lambda x: {
            "qa": "💬 Q&A (Natural Language)",
            "extraction": "📋 Extraction (Structured Data)",
            "sources_only": "🔍 Sources Only",
        }.get(x, x),
    )
    
    st.divider()
    
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()


# Chat Interface
st.header("💬 Chat")

# Display messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Show sources if available
        if "sources" in message and message["sources"]:
            with st.expander("📚 Sources"):
                for i, source in enumerate(message["sources"]):
                    st.write(f"**{i+1}. {source.get('source_file', 'Unknown')}** (Page {source.get('page', '?')})")
                    st.caption(source.get("text", "")[:300])
                    st.divider()

# Chat input
if prompt := st.chat_input("Ask about your construction documents..."):
    # Check if we have indexed docs
    if not st.session_state.indexed_docs:
        st.warning("⚠️ Please upload and process a document first!")
    else:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = local_chat_query(prompt, mode=mode)
                    
                    answer = response.get("answer", "I couldn't find an answer.")
                    sources = response.get("sources", [])
                    
                    st.markdown(answer)
                    
                    # Show sources
                    if sources:
                        with st.expander("📚 Sources"):
                            for i, source in enumerate(sources):
                                st.write(f"**{i+1}. {source.get('source_file', 'Unknown')}** (Page {source.get('page', '?')})")
                                st.caption(source.get("text", "")[:300])
                                st.divider()
                    
                    # Save to history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "sources": sources,
                    })
                    
                except Exception as e:
                    st.error(f"Error: {e}")
                    logger.exception("Query error")


# Footer
st.divider()
st.caption("Built for Constructure AI Technical Assignment | Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025")
