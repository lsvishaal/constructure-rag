"""
Evaluation API endpoints.

Run evaluation queries through the RAG pipeline and return results.

Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
"""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Response, HTTPException, Query

from src.core.config import PROJECT_CONTEXT_ID, BUILD_WATERMARK, settings
from src.models.auth import User
from src.services.auth import get_current_active_user
from src.services.embeddings import EmbeddingService
from src.services.vector_store import VectorStoreService
from src.services.retrieval import RetrievalService
from src.services.rag_pipeline import RAGPipeline
from src.services.evaluation import EvaluationRunner, TEST_QUERIES

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/evaluation", tags=["Evaluation"])


# =============================================================================
# Service Dependencies (lazy initialization)
# =============================================================================

_embedding_service = None
_vector_store = None
_retrieval_service = None
_rag_pipeline = None


def get_embedding_service() -> EmbeddingService:
    """Get or create embedding service (singleton)."""
    global _embedding_service
    if _embedding_service is None:
        logger.info(f"[{PROJECT_CONTEXT_ID}] Initializing EmbeddingService...")
        _embedding_service = EmbeddingService()
    return _embedding_service


def get_vector_store() -> VectorStoreService:
    """Get or create vector store (singleton)."""
    global _vector_store
    if _vector_store is None:
        logger.info(f"[{PROJECT_CONTEXT_ID}] Connecting to Qdrant...")
        _vector_store = VectorStoreService(
            url=settings.qdrant_url,
            collection_name=settings.qdrant_collection,
            use_memory=False
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
            ollama_model=settings.ollama_model
        )
    return _rag_pipeline


# =============================================================================
# Evaluation Endpoints
# =============================================================================

@router.get("/queries")
async def list_test_queries(
    response: Response,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """
    List all predefined test queries for evaluation.
    
    Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
    """
    response.headers["X-Project-Id"] = PROJECT_CONTEXT_ID
    response.headers["X-Build-Watermark"] = BUILD_WATERMARK
    
    return {
        "total_queries": len(TEST_QUERIES),
        "queries": TEST_QUERIES,
        "watermark": BUILD_WATERMARK,
    }


@router.post("/run")
async def run_evaluation(
    response: Response,
    current_user: Annotated[User, Depends(get_current_active_user)],
    llm_provider: str = Query(default=None, description="LLM provider override"),
    limit: int = Query(default=None, ge=1, le=len(TEST_QUERIES), description="Limit number of queries"),
) -> dict:
    """
    Run evaluation against the indexed documents.
    
    Runs test queries through the RAG pipeline and scores the results.
    
    Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
    """
    response.headers["X-Project-Id"] = PROJECT_CONTEXT_ID
    response.headers["X-Build-Watermark"] = BUILD_WATERMARK
    
    try:
        # Check if documents are indexed
        vector_store = get_vector_store()
        doc_count = vector_store.count()
        
        if doc_count == 0:
            return {
                "status": "error",
                "message": "No documents indexed. Please ingest documents first.",
                "watermark": BUILD_WATERMARK,
            }
        
        # Get or create RAG pipeline
        pipeline = get_rag_pipeline()
        
        # Override LLM if specified
        if llm_provider:
            pipeline = RAGPipeline(
                retrieval_service=get_retrieval_service(),
                llm_provider=llm_provider,
                ollama_url=settings.ollama_base_url,
                ollama_model=settings.ollama_model
            )
        
        # Select queries
        queries = TEST_QUERIES[:limit] if limit else TEST_QUERIES
        
        # Run evaluation
        logger.info(f"[{PROJECT_CONTEXT_ID}] Running evaluation with {len(queries)} queries")
        
        runner = EvaluationRunner(rag_pipeline=pipeline, queries=queries)
        report = runner.run()
        
        return {
            "status": "completed",
            "documents_indexed": doc_count,
            "llm_provider": llm_provider or settings.llm_provider,
            "report": report,
            "watermark": BUILD_WATERMARK,
        }
        
    except Exception as e:
        logger.error(f"[{PROJECT_CONTEXT_ID}] Evaluation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Evaluation error: {str(e)}"
        )


@router.post("/score")
async def score_single_query(
    response: Response,
    current_user: Annotated[User, Depends(get_current_active_user)],
    question: str = Query(..., description="Question to evaluate"),
    expected_keywords: str = Query(default="", description="Comma-separated expected keywords"),
) -> dict:
    """
    Run a single query and score the result.
    
    Useful for testing specific questions.
    
    Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
    """
    response.headers["X-Project-Id"] = PROJECT_CONTEXT_ID
    response.headers["X-Build-Watermark"] = BUILD_WATERMARK
    
    try:
        pipeline = get_rag_pipeline()
        
        # Run query
        rag_response = pipeline.query(question, top_k=5)
        
        # Score
        keywords = [k.strip() for k in expected_keywords.split(",") if k.strip()]
        runner = EvaluationRunner(rag_pipeline=None)
        score = runner.score_answer(rag_response.answer, keywords)
        
        return {
            "question": question,
            "answer": rag_response.answer,
            "expected_keywords": keywords,
            "score": score,
            "citations": [
                {
                    "source_file": c.source_file,
                    "page": c.page,
                    "score": c.score
                }
                for c in rag_response.citations
            ],
            "watermark": BUILD_WATERMARK,
        }
        
    except Exception as e:
        logger.error(f"[{PROJECT_CONTEXT_ID}] Score query error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error: {str(e)}"
        )
