"""
Chat API endpoints (RAG Q&A).

Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
"""
import logging
import time
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, HTTPException

from src.core.config import PROJECT_CONTEXT_ID, BUILD_WATERMARK, settings
from src.models.auth import User
from src.models.chat import ChatRequest, ChatResponse, Source
from src.services.auth import get_current_active_user
from src.services.embeddings import EmbeddingService
from src.services.vector_store import VectorStoreService
from src.services.retrieval import RetrievalService
from src.services.rag_pipeline import RAGPipeline
from src.services.extraction import ExtractionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


# =============================================================================
# Service Dependencies (lazy initialization)
# =============================================================================

_embedding_service = None
_vector_store = None
_retrieval_service = None
_rag_pipeline = None
_extraction_service = None


def get_embedding_service() -> EmbeddingService:
    """Get or create embedding service (singleton)."""
    global _embedding_service
    if _embedding_service is None:
        logger.info(f"[{PROJECT_CONTEXT_ID}] Initializing EmbeddingService...")
        _embedding_service = EmbeddingService()
    return _embedding_service


def get_vector_store() -> VectorStoreService:
    """Get or create vector store (singleton, connects to Qdrant)."""
    global _vector_store
    if _vector_store is None:
        logger.info(f"[{PROJECT_CONTEXT_ID}] Connecting to Qdrant...")
        _vector_store = VectorStoreService(
            url=settings.qdrant_url,
            collection_name=settings.qdrant_collection,
            use_memory=False  # Use actual Qdrant server
        )
    return _vector_store


def get_retrieval_service() -> RetrievalService:
    """Get or create retrieval service (singleton)."""
    global _retrieval_service
    if _retrieval_service is None:
        _retrieval_service = RetrievalService(
            embedding_service=get_embedding_service(),
            vector_store=get_vector_store()
        )
    return _retrieval_service


def get_rag_pipeline() -> RAGPipeline:
    """Get or create RAG pipeline (singleton)."""
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = RAGPipeline(
            retrieval_service=get_retrieval_service(),
            llm_provider=settings.llm_provider,
            ollama_url=settings.ollama_base_url,
            ollama_model=settings.ollama_model,
        )
    return _rag_pipeline


def get_extraction_service() -> ExtractionService:
    """Get or create extraction service (singleton)."""
    global _extraction_service
    if _extraction_service is None:
        _extraction_service = ExtractionService(
            retrieval_service=get_retrieval_service(),
            llm_provider=settings.llm_provider,
            ollama_url=settings.ollama_base_url,
            ollama_model=settings.ollama_model,
        )
    return _extraction_service


# =============================================================================
# Chat Endpoints
# =============================================================================

@router.post("", response_model=ChatResponse)
async def chat(
    response: Response,
    request: ChatRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> ChatResponse:
    """
    Chat endpoint for RAG Q&A.
    
    Supports three modes:
    - qa: Natural language question answering with sources
    - extraction: Structured data extraction (triggers special prompts)
    - sources_only: Return relevant sources without LLM generation
    
    Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
    """
    response.headers["X-Project-Id"] = PROJECT_CONTEXT_ID
    response.headers["X-Build-Watermark"] = BUILD_WATERMARK
    
    start_time = time.time()
    conversation_id = request.conversation_id or str(uuid.uuid4())
    
    logger.info(f"[{PROJECT_CONTEXT_ID}] Chat request: mode={request.mode}, message='{request.message[:50]}...'")
    
    try:
        if request.mode == "qa":
            # Standard Q&A with RAG pipeline (async, hybrid search enabled)
            rag_response = await get_rag_pipeline().query_async(
                question=request.message,
                top_k=5,
                use_keyword_search=True  # Enable hybrid search for better results
            )
            
            # Convert citations to Source objects
            sources = [
                Source(
                    file_name=c.source_file,
                    page_number=c.page,
                    section_title=None,
                    snippet=c.text[:500],
                    relevance_score=c.score
                )
                for c in rag_response.citations
            ]
            
            processing_time = (time.time() - start_time) * 1000
            
            return ChatResponse(
                answer=rag_response.answer,
                sources=sources,
                conversation_id=conversation_id,
                mode=request.mode,
                processing_time_ms=processing_time,
                chunks_retrieved=len(rag_response.citations),
            )
            
        elif request.mode == "extraction":
            # Structured data extraction (async)
            # Detect data type from query
            data_type = "generic"
            message_lower = request.message.lower()
            if "door" in message_lower:
                data_type = "door_schedule"
            elif "window" in message_lower:
                data_type = "window_schedule"
            elif "wage" in message_lower or "labor" in message_lower or "rate" in message_lower or "classification" in message_lower:
                data_type = "wage_table"
            
            extraction_result = await get_extraction_service().extract_async(
                query=request.message,
                data_type=data_type,
                top_k=10
            )
            
            # Convert sources
            sources = [
                Source(
                    file_name=s.source_file,
                    page_number=s.page or 0,
                    section_title=None,
                    snippet=s.text_snippet[:500],
                    relevance_score=0.0
                )
                for s in extraction_result.sources
            ]
            
            processing_time = (time.time() - start_time) * 1000
            
            # Determine extraction type for frontend
            extraction_type = "wage_table" if data_type == "wage_table" else "door_schedule" if data_type == "door_schedule" else "custom"
            
            return ChatResponse(
                answer=f"Extracted {len(extraction_result.entries)} {data_type.replace('_', ' ')} entries.",
                sources=sources,
                conversation_id=conversation_id,
                mode=request.mode,
                processing_time_ms=processing_time,
                chunks_retrieved=len(sources),
                structured_data={
                    "extraction_type": extraction_type,
                    "entries": extraction_result.entries,
                    "count": len(extraction_result.entries)
                },
            )
            
        elif request.mode == "sources_only":
            # Just retrieve relevant chunks without LLM (async)
            retrieval_results = await get_retrieval_service().retrieve_async(
                query=request.message,
                top_k=10
            )
            
            sources = [
                Source(
                    file_name=r.metadata.get("source_file", "unknown"),
                    page_number=r.metadata.get("page", 0),
                    section_title=None,
                    snippet=r.text[:500],
                    relevance_score=r.score
                )
                for r in retrieval_results
            ]
            
            processing_time = (time.time() - start_time) * 1000
            
            return ChatResponse(
                answer=f"Found {len(sources)} relevant sources.",
                sources=sources,
                conversation_id=conversation_id,
                mode=request.mode,
                processing_time_ms=processing_time,
                chunks_retrieved=len(sources),
            )
            
        else:
            raise HTTPException(status_code=400, detail=f"Unknown mode: {request.mode}")
            
    except Exception as e:
        logger.error(f"[{PROJECT_CONTEXT_ID}] Chat error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Chat processing error: {str(e)}"
        )
