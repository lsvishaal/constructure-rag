"""
FastAPI Application - Constructure RAG Project Brain.

Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.core.config import settings, PROJECT_CONTEXT_ID, BUILD_WATERMARK
from src.api.auth import router as auth_router
from src.api.chat import router as chat_router
from src.api.documents import router as documents_router
from src.api.health import router as health_router
from src.api.evaluation import router as evaluation_router

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format=f"[{PROJECT_CONTEXT_ID}] %(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
# Suppress verbose logging from PDF parsing libraries
logging.getLogger("pdfminer").setLevel(logging.WARNING)
logging.getLogger("pdfplumber").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info(f"[{PROJECT_CONTEXT_ID}] Starting Constructure RAG API")
    logger.info(f"[{PROJECT_CONTEXT_ID}] Watermark: {BUILD_WATERMARK}")
    logger.info(f"[{PROJECT_CONTEXT_ID}] LLM Provider: {settings.llm_provider}")
    logger.info(f"[{PROJECT_CONTEXT_ID}] Embedding Provider: {settings.embedding_provider}")
    
    # Warmup: Pre-load the Ollama model to avoid cold start delay
    if settings.llm_provider == "ollama":
        await warmup_ollama_model()
    
    yield
    
    # Shutdown
    logger.info(f"[{PROJECT_CONTEXT_ID}] Shutting down Constructure RAG API")


async def warmup_ollama_model():
    """
    Pre-load the Ollama model to avoid cold start delay on first request.
    This sends a tiny request to load the model into memory.
    """
    import httpx
    
    logger.info(f"[{PROJECT_CONTEXT_ID}] Warming up Ollama model: {settings.ollama_model}")
    
    try:
        async with httpx.AsyncClient() as client:
            # Send a minimal request to load the model
            response = await client.post(
                f"{settings.ollama_base_url}/api/generate",
                json={
                    "model": settings.ollama_model,
                    "prompt": "Hi",
                    "stream": False,
                    "keep_alive": "10m",  # Keep model loaded for 10 minutes
                    "options": {
                        "num_predict": 1,  # Generate just 1 token
                    }
                },
                timeout=60.0  # Allow up to 60s for model loading
            )
            response.raise_for_status()
            logger.info(f"[{PROJECT_CONTEXT_ID}] ✓ Ollama model warmed up successfully")
    except httpx.ConnectError:
        logger.warning(f"[{PROJECT_CONTEXT_ID}] ⚠ Could not connect to Ollama - model will load on first request")
    except Exception as e:
        logger.warning(f"[{PROJECT_CONTEXT_ID}] ⚠ Ollama warmup failed: {e} - model will load on first request")


# Create FastAPI app
app = FastAPI(
    title="Constructure RAG API",
    description=f"""
    Project Brain for Construction Documents.
    
    A RAG-powered system for querying construction project documents,
    extracting structured data (door schedules, wage tables), and
    providing source-backed answers.
    
    **Project ID:** {PROJECT_CONTEXT_ID}
    **Watermark:** {BUILD_WATERMARK}
    
    ## Features
    - PDF document ingestion and indexing
    - Natural language Q&A with source citations
    - Structured data extraction (door schedules, wage tables)
    - Hybrid retrieval (vector + keyword search)
    
    ## Authentication
    Use the `/api/v1/auth/token` endpoint to get a JWT token.
    Include the token in the `Authorization` header as `Bearer <token>`.
    
    Test credentials:
    - Email: `testingcheckuser1234@gmail.com`
    - Password: `constructure2024`
    """,
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Project-Id", "X-Build-Watermark"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    logger.error(f"[{PROJECT_CONTEXT_ID}] Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "watermark": BUILD_WATERMARK,
        },
        headers={
            "X-Project-Id": PROJECT_CONTEXT_ID,
            "X-Build-Watermark": BUILD_WATERMARK,
        }
    )


# Add watermark header to all responses
@app.middleware("http")
async def add_watermark_header(request: Request, call_next):
    """Add watermark headers to all responses."""
    response: Response = await call_next(request)
    response.headers["X-Project-Id"] = PROJECT_CONTEXT_ID
    response.headers["X-Build-Watermark"] = BUILD_WATERMARK
    return response


# Include routers
app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(evaluation_router, prefix="/api/v1")


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Constructure RAG API",
        "version": "0.1.0",
        "description": "Project Brain for Construction Documents",
        "project_id": PROJECT_CONTEXT_ID,
        "watermark": BUILD_WATERMARK,
        "docs": "/docs",
        "health": "/api/v1/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
