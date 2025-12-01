"""
Health check endpoints.

Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Response

from src.core.config import settings, PROJECT_CONTEXT_ID, BUILD_WATERMARK

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
async def health_check(response: Response):
    """Basic health check endpoint."""
    response.headers["X-Project-Id"] = PROJECT_CONTEXT_ID
    response.headers["X-Build-Watermark"] = BUILD_WATERMARK
    
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project_id": PROJECT_CONTEXT_ID,
        "watermark": BUILD_WATERMARK,
        "version": "0.1.0",
    }


@router.get("/ready")
async def readiness_check(response: Response):
    """Readiness check - verifies all dependencies are ready."""
    response.headers["X-Project-Id"] = PROJECT_CONTEXT_ID
    response.headers["X-Build-Watermark"] = BUILD_WATERMARK
    
    # TODO: Check Qdrant connection, LLM availability, etc.
    checks = {
        "database": "ok",
        "llm_provider": settings.llm_provider,
        "embedding_provider": settings.embedding_provider,
    }
    
    return {
        "status": "ready",
        "checks": checks,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "watermark": BUILD_WATERMARK,
    }
