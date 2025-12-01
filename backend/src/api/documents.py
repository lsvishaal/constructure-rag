"""
Document API endpoints (ingestion, indexing).

Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
"""
import json
import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Response, UploadFile, File, HTTPException, Query

from src.core.config import PROJECT_CONTEXT_ID, BUILD_WATERMARK, settings
from src.models.auth import User
from src.services.auth import get_current_active_user
from src.services.pdf_parser import PDFParser
from src.services.chunking import ChunkingService
from src.services.embeddings import EmbeddingService, EmbeddedChunk
from src.services.vector_store import VectorStoreService
from src.services.smart_parser import SmartPDFParser
from src.services.smart_chunker import SmartChunker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])


# =============================================================================
# Service Dependencies (lazy initialization)
# =============================================================================

_pdf_parser = None
_chunking_service = None
_embedding_service = None
_vector_store = None


def get_pdf_parser() -> PDFParser:
    """Get or create PDF parser (singleton)."""
    global _pdf_parser
    if _pdf_parser is None:
        _pdf_parser = PDFParser()
    return _pdf_parser


def get_chunking_service() -> ChunkingService:
    """Get or create chunking service (singleton)."""
    global _chunking_service
    if _chunking_service is None:
        _chunking_service = ChunkingService(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )
    return _chunking_service


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
            use_memory=False
        )
    return _vector_store


# =============================================================================
# Document Endpoints
# =============================================================================

@router.get("")
async def list_documents(
    response: Response,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """
    List all ingested documents and collection statistics.
    
    Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
    """
    response.headers["X-Project-Id"] = PROJECT_CONTEXT_ID
    response.headers["X-Build-Watermark"] = BUILD_WATERMARK
    
    try:
        vector_store = get_vector_store()
        count = vector_store.count()
        
        return {
            "documents": [],  # TODO: Track ingested filenames
            "total_chunks": count,
            "collection": settings.qdrant_collection,
            "watermark": BUILD_WATERMARK,
        }
    except Exception as e:
        logger.error(f"[{PROJECT_CONTEXT_ID}] Error listing documents: {e}")
        return {
            "documents": [],
            "total_chunks": 0,
            "error": str(e),
            "watermark": BUILD_WATERMARK,
        }


@router.post("/ingest")
async def ingest_documents(
    response: Response,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """
    Ingest all PDF documents from the Assets directory.
    
    Parses PDFs, chunks text, generates embeddings, and stores in vector DB.
    
    Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
    """
    response.headers["X-Project-Id"] = PROJECT_CONTEXT_ID
    response.headers["X-Build-Watermark"] = BUILD_WATERMARK
    
    start_time = time.time()
    
    # Find Assets directory - try configured path first, then fallbacks
    assets_dir = Path(settings.data_dir)
    logger.info(f"[{PROJECT_CONTEXT_ID}] Looking for assets at: {assets_dir}")
    
    if not assets_dir.exists():
        # Try /app/Assets for Docker
        assets_dir = Path("/app/Assets")
        logger.info(f"[{PROJECT_CONTEXT_ID}] Trying Docker path: {assets_dir}")
    
    if not assets_dir.exists():
        # Try relative to current file for local dev
        assets_dir = Path(__file__).parent.parent.parent.parent / "Assets"
        logger.info(f"[{PROJECT_CONTEXT_ID}] Trying local path: {assets_dir}")
    
    if not assets_dir.exists():
        raise HTTPException(status_code=404, detail=f"Assets directory not found. Tried: {settings.data_dir}, /app/Assets")
    
    # Find all PDFs
    pdf_files = list(assets_dir.glob("*.pdf"))
    if not pdf_files:
        return {
            "status": "warning",
            "message": "No PDF files found in Assets directory",
            "assets_dir": str(assets_dir),
            "watermark": BUILD_WATERMARK,
        }
    
    logger.info(f"[{PROJECT_CONTEXT_ID}] Found {len(pdf_files)} PDF files to ingest")
    
    results = []
    total_chunks = 0
    
    pdf_parser = get_pdf_parser()
    chunking_service = get_chunking_service()
    embedding_service = get_embedding_service()
    vector_store = get_vector_store()
    
    for pdf_path in pdf_files:
        file_start = time.time()
        try:
            # Parse PDF
            logger.info(f"[{PROJECT_CONTEXT_ID}] Parsing {pdf_path.name}...")
            parsed = pdf_parser.parse(str(pdf_path))
            
            # Chunk all pages
            all_chunks = []
            for page in parsed.pages:
                page_chunks = chunking_service.chunk(
                    text=page.text,
                    source_file=parsed.filename,
                    page=page.page_number
                )
                all_chunks.extend(page_chunks)
            
            logger.info(f"[{PROJECT_CONTEXT_ID}] Created {len(all_chunks)} chunks from {pdf_path.name}")
            
            # Embed and store chunks
            for chunk in all_chunks:
                vector = embedding_service.embed(chunk.text)
                embedded = EmbeddedChunk(
                    text=chunk.text,
                    vector=vector,
                    metadata={
                        "source_file": chunk.source_file,
                        "page": chunk.page,
                        "chunk_index": chunk.chunk_index,
                        "section": chunk.section,
                    },
                    watermark=PROJECT_CONTEXT_ID
                )
                vector_store.store(embedded)
            
            file_time = time.time() - file_start
            results.append({
                "filename": pdf_path.name,
                "pages": parsed.page_count,
                "chunks": len(all_chunks),
                "time_seconds": round(file_time, 2),
                "status": "success"
            })
            total_chunks += len(all_chunks)
            
        except Exception as e:
            logger.error(f"[{PROJECT_CONTEXT_ID}] Error ingesting {pdf_path.name}: {e}", exc_info=True)
            results.append({
                "filename": pdf_path.name,
                "error": str(e),
                "status": "error"
            })
    
    total_time = time.time() - start_time
    
    return {
        "status": "completed",
        "files_processed": len(pdf_files),
        "total_chunks": total_chunks,
        "total_time_seconds": round(total_time, 2),
        "results": results,
        "watermark": BUILD_WATERMARK,
    }


@router.post("/upload")
async def upload_document(
    response: Response,
    file: UploadFile = File(...),
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
) -> dict:
    """
    Upload and ingest a single PDF document.
    
    Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
    """
    response.headers["X-Project-Id"] = PROJECT_CONTEXT_ID
    response.headers["X-Build-Watermark"] = BUILD_WATERMARK
    
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    start_time = time.time()
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            pdf_parser = get_pdf_parser()
            chunking_service = get_chunking_service()
            embedding_service = get_embedding_service()
            vector_store = get_vector_store()
            
            # Parse PDF
            logger.info(f"[{PROJECT_CONTEXT_ID}] Parsing uploaded file: {file.filename}")
            parsed = pdf_parser.parse(tmp_path, original_filename=file.filename)
            
            # Chunk all pages
            all_chunks = []
            for page in parsed.pages:
                page_chunks = chunking_service.chunk(
                    text=page.text,
                    source_file=file.filename,
                    page=page.page_number
                )
                all_chunks.extend(page_chunks)
            
            logger.info(f"[{PROJECT_CONTEXT_ID}] Created {len(all_chunks)} chunks from {file.filename}")
            
            # Embed and store chunks
            for chunk in all_chunks:
                vector = embedding_service.embed(chunk.text)
                embedded = EmbeddedChunk(
                    text=chunk.text,
                    vector=vector,
                    metadata={
                        "source_file": chunk.source_file,
                        "page": chunk.page,
                        "chunk_index": chunk.chunk_index,
                        "section": chunk.section,
                    },
                    watermark=PROJECT_CONTEXT_ID
                )
                vector_store.store(embedded)
            
            total_time = time.time() - start_time
            
            return {
                "status": "success",
                "filename": file.filename,
                "pages": parsed.page_count,
                "chunks": len(all_chunks),
                "time_seconds": round(total_time, 2),
                "watermark": BUILD_WATERMARK,
            }
            
        finally:
            # Clean up temp file
            os.unlink(tmp_path)
            
    except Exception as e:
        logger.error(f"[{PROJECT_CONTEXT_ID}] Error uploading {file.filename}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {str(e)}"
        )


@router.delete("")
async def clear_documents(
    response: Response,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """
    Clear all documents from the vector store.
    
    Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
    """
    response.headers["X-Project-Id"] = PROJECT_CONTEXT_ID
    response.headers["X-Build-Watermark"] = BUILD_WATERMARK
    
    try:
        vector_store = get_vector_store()
        vector_store.delete_collection()
        
        return {
            "status": "success",
            "message": "All documents cleared from vector store",
            "watermark": BUILD_WATERMARK,
        }
    except Exception as e:
        logger.error(f"[{PROJECT_CONTEXT_ID}] Error clearing documents: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing documents: {str(e)}"
        )


# =============================================================================
# Smart Ingestion Endpoints (uses structured parsing)
# =============================================================================

_smart_parser = None
_smart_chunker = None


def get_smart_parser() -> SmartPDFParser:
    """Get or create smart PDF parser (singleton)."""
    global _smart_parser
    if _smart_parser is None:
        _smart_parser = SmartPDFParser()
    return _smart_parser


def get_smart_chunker() -> SmartChunker:
    """Get or create smart chunker (singleton)."""
    global _smart_chunker
    if _smart_chunker is None:
        _smart_chunker = SmartChunker(chunk_size=settings.chunk_size)
    return _smart_chunker


@router.post("/smart-ingest")
async def smart_ingest_documents(
    response: Response,
    current_user: Annotated[User, Depends(get_current_active_user)],
    project_id: str = Query(default="default", description="Project identifier"),
) -> dict:
    """
    Smart ingest all PDFs using structured parsing.
    
    This uses the new SmartPDFParser that:
    - Treats PDFs as structured datasets (sheets + pages)
    - Extracts sheet IDs and disciplines
    - Handles image-only pages gracefully
    - Chunks per page (never across page boundaries)
    
    Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
    """
    response.headers["X-Project-Id"] = PROJECT_CONTEXT_ID
    response.headers["X-Build-Watermark"] = BUILD_WATERMARK
    
    start_time = time.time()
    
    # Find Assets directory
    assets_dir = Path(settings.data_dir)
    if not assets_dir.exists():
        assets_dir = Path("/app/Assets")
    if not assets_dir.exists():
        assets_dir = Path(__file__).parent.parent.parent.parent / "Assets"
    
    if not assets_dir.exists():
        raise HTTPException(status_code=404, detail="Assets directory not found")
    
    pdf_files = list(assets_dir.glob("*.pdf"))
    if not pdf_files:
        return {
            "status": "warning",
            "message": "No PDF files found",
            "watermark": BUILD_WATERMARK,
        }
    
    logger.info(f"[{PROJECT_CONTEXT_ID}] Smart ingesting {len(pdf_files)} files for project {project_id}")
    
    smart_parser = get_smart_parser()
    smart_chunker = get_smart_chunker()
    embedding_service = get_embedding_service()
    vector_store = get_vector_store()
    
    results = []
    total_chunks = 0
    total_pages = 0
    total_text_pages = 0
    total_image_only = 0
    
    for pdf_path in pdf_files:
        file_start = time.time()
        try:
            # Smart parse
            logger.info(f"[{PROJECT_CONTEXT_ID}] Smart parsing {pdf_path.name}...")
            document = smart_parser.parse(str(pdf_path), project_id=project_id)
            
            # Smart chunk
            chunks = smart_chunker.chunk_document(document)
            logger.info(f"[{PROJECT_CONTEXT_ID}] Created {len(chunks)} smart chunks")
            
            # Embed and store
            indexed = 0
            for chunk in chunks:
                try:
                    vector = embedding_service.embed(chunk.text)
                    embedded = EmbeddedChunk(
                        text=chunk.text,
                        vector=vector,
                        metadata=chunk.to_metadata_dict(),
                        watermark=PROJECT_CONTEXT_ID
                    )
                    vector_store.store(embedded)
                    indexed += 1
                except Exception as e:
                    logger.warning(f"[{PROJECT_CONTEXT_ID}] Failed to index chunk: {e}")
            
            file_time = time.time() - file_start
            results.append({
                "filename": pdf_path.name,
                "document_type": document.document_type,
                "total_pages": document.total_pages,
                "text_pages": document.text_pages,
                "image_only_pages": document.image_only_pages,
                "chunks": len(chunks),
                "indexed": indexed,
                "time_seconds": round(file_time, 2),
                "status": "success"
            })
            
            total_chunks += indexed
            total_pages += document.total_pages
            total_text_pages += document.text_pages
            total_image_only += document.image_only_pages
            
        except Exception as e:
            logger.error(f"[{PROJECT_CONTEXT_ID}] Error smart-ingesting {pdf_path.name}: {e}", exc_info=True)
            results.append({
                "filename": pdf_path.name,
                "error": str(e),
                "status": "error"
            })
    
    total_time = time.time() - start_time
    
    return {
        "status": "completed",
        "project_id": project_id,
        "files_processed": len(pdf_files),
        "total_pages": total_pages,
        "text_pages": total_text_pages,
        "image_only_pages": total_image_only,
        "total_chunks": total_chunks,
        "total_time_seconds": round(total_time, 2),
        "results": results,
        "watermark": BUILD_WATERMARK,
    }


@router.get("/ingestion-report")
async def get_ingestion_report(
    response: Response,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """
    Get the latest ingestion report (from CLI or API ingestion).
    
    Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
    """
    response.headers["X-Project-Id"] = PROJECT_CONTEXT_ID
    response.headers["X-Build-Watermark"] = BUILD_WATERMARK
    
    # Try to find report file
    report_paths = [
        Path("./data/parsed/ingestion_report.json"),
        Path("/app/data/parsed/ingestion_report.json"),
    ]
    
    for report_path in report_paths:
        if report_path.exists():
            try:
                with open(report_path) as f:
                    report = json.load(f)
                return {
                    "status": "found",
                    "report_path": str(report_path),
                    "report": report,
                    "watermark": BUILD_WATERMARK,
                }
            except Exception as e:
                logger.error(f"Error reading report: {e}")
    
    # No report file - return current vector store stats
    try:
        vector_store = get_vector_store()
        count = vector_store.count()
        
        return {
            "status": "no_report",
            "message": "No ingestion report file found. Use CLI for full reports.",
            "current_stats": {
                "collection": settings.qdrant_collection,
                "total_chunks": count,
            },
            "watermark": BUILD_WATERMARK,
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "watermark": BUILD_WATERMARK,
        }
