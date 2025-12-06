"""
Vector Store Service - Phase 2 (Async Optimized)

Qdrant vector database integration for storing and searching embeddings.
Fully async with connection pooling and concurrent operations.

Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
"""
from dataclasses import dataclass
from typing import Any
from concurrent.futures import ThreadPoolExecutor
import asyncio
import uuid
import logging

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
)

from src.core.config import PROJECT_CONTEXT_ID
from src.services.embeddings import EmbeddedChunk

logger = logging.getLogger(__name__)

# Global thread pool for I/O-bound Qdrant operations
_qdrant_executor: ThreadPoolExecutor | None = None

def get_qdrant_executor() -> ThreadPoolExecutor:
    """Get or create a thread pool for Qdrant operations."""
    global _qdrant_executor
    if _qdrant_executor is None:
        # More workers for I/O-bound operations
        _qdrant_executor = ThreadPoolExecutor(max_workers=8, thread_name_prefix="qdrant")
    return _qdrant_executor


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class StoredDocument:
    """
    A document retrieved from the vector store.
    
    Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
    """
    id: str
    text: str
    score: float
    metadata: dict[str, Any]
    watermark: str = PROJECT_CONTEXT_ID


# =============================================================================
# Vector Store Service (Async Optimized)
# =============================================================================

class VectorStoreService:
    """
    Service for storing and searching document embeddings in Qdrant.
    
    Supports both in-memory mode (for testing) and server mode (production).
    
    Async features:
    - Non-blocking search and store operations
    - Thread pool for I/O-bound Qdrant calls
    - Batch operations for efficiency
    
    Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
    """
    
    DEFAULT_COLLECTION = "constructure_rag"
    TEST_COLLECTION = "constructure_rag_test"
    VECTOR_DIMENSION = 384  # BGE-small-en-v1.5 dimension
    
    def __init__(
        self,
        url: str = "http://localhost:6333",
        collection_name: str | None = None,
        use_memory: bool = False,
        watermark: str = PROJECT_CONTEXT_ID
    ):
        """
        Initialize vector store service.
        
        Args:
            url: Qdrant server URL (ignored if use_memory=True)
            collection_name: Collection name (default based on mode)
            use_memory: Use in-memory storage for testing
            watermark: Project watermark identifier
        """
        self.watermark = watermark
        self._use_memory = use_memory
        
        # Set collection name based on mode
        if collection_name:
            self._collection_name = collection_name
        else:
            self._collection_name = self.TEST_COLLECTION if use_memory else self.DEFAULT_COLLECTION
        
        # Initialize Qdrant client
        if use_memory:
            self._client = QdrantClient(":memory:")
            logger.info(f"[{self.watermark}] VectorStore initialized in-memory mode")
        else:
            self._client = QdrantClient(url=url, check_compatibility=False)
            logger.info(f"[{self.watermark}] VectorStore connected to {url}")
        
        # Ensure collection exists
        self._ensure_collection()
    
    @property
    def collection_name(self) -> str:
        """Return collection name."""
        return self._collection_name
    
    def _ensure_collection(self) -> None:
        """Create collection if it doesn't exist."""
        collections = self._client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if self._collection_name not in collection_names:
            self._client.create_collection(
                collection_name=self._collection_name,
                vectors_config=VectorParams(
                    size=self.VECTOR_DIMENSION,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"[{self.watermark}] Created collection: {self._collection_name}")
    
    def store(self, chunk: EmbeddedChunk) -> str:
        """
        Store a single embedded chunk (sync).
        
        Args:
            chunk: EmbeddedChunk to store
            
        Returns:
            Document ID
        """
        doc_id = str(uuid.uuid4())
        
        # Build payload with watermark
        payload = {
            "text": chunk.text,
            "watermark": self.watermark,
            **chunk.metadata
        }
        
        point = PointStruct(
            id=doc_id,
            vector=chunk.vector.tolist(),
            payload=payload
        )
        
        self._client.upsert(
            collection_name=self._collection_name,
            points=[point]
        )
        
        logger.debug(f"[{self.watermark}] Stored document: {doc_id}")
        return doc_id
    
    async def store_async(self, chunk: EmbeddedChunk) -> str:
        """
        Store a single embedded chunk (async).
        
        Args:
            chunk: EmbeddedChunk to store
            
        Returns:
            Document ID
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(get_qdrant_executor(), self.store, chunk)
    
    def store_batch(self, chunks: list[EmbeddedChunk]) -> list[str]:
        """
        Store multiple embedded chunks efficiently (sync).
        
        Args:
            chunks: List of EmbeddedChunk objects
            
        Returns:
            List of document IDs
        """
        if not chunks:
            return []
        
        doc_ids = []
        points = []
        
        for chunk in chunks:
            doc_id = str(uuid.uuid4())
            doc_ids.append(doc_id)
            
            payload = {
                "text": chunk.text,
                "watermark": self.watermark,
                **chunk.metadata
            }
            
            points.append(PointStruct(
                id=doc_id,
                vector=chunk.vector.tolist(),
                payload=payload
            ))
        
        self._client.upsert(
            collection_name=self._collection_name,
            points=points
        )
        
        logger.info(f"[{self.watermark}] Stored {len(chunks)} documents")
        return doc_ids
    
    async def store_batch_async(self, chunks: list[EmbeddedChunk]) -> list[str]:
        """
        Store multiple embedded chunks efficiently (async).
        
        Args:
            chunks: List of EmbeddedChunk objects
            
        Returns:
            List of document IDs
        """
        if not chunks:
            return []
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            get_qdrant_executor(),
            self.store_batch,
            chunks
        )
    
    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 5,
        score_threshold: float | None = None
    ) -> list[StoredDocument]:
        """
        Search for similar documents (sync).
        
        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            score_threshold: Minimum similarity score (optional)
            
        Returns:
            List of StoredDocument objects
        """
        # Use query_points (new API) instead of deprecated search
        search_result = self._client.query_points(
            collection_name=self._collection_name,
            query=query_vector.tolist(),
            limit=top_k,
            score_threshold=score_threshold
        )
        
        results = []
        for point in search_result.points:
            payload = dict(point.payload) if point.payload else {}
            
            # Extract text and metadata
            text = payload.pop("text", "")
            watermark = payload.pop("watermark", self.watermark)
            
            results.append(StoredDocument(
                id=str(point.id),
                text=text,
                score=point.score,
                metadata=payload,
                watermark=watermark
            ))
        
        logger.debug(f"[{self.watermark}] Search returned {len(results)} results")
        return results
    
    async def search_async(
        self,
        query_vector: np.ndarray,
        top_k: int = 5,
        score_threshold: float | None = None
    ) -> list[StoredDocument]:
        """
        Search for similar documents (async).
        
        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            score_threshold: Minimum similarity score (optional)
            
        Returns:
            List of StoredDocument objects
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            get_qdrant_executor(),
            lambda: self.search(query_vector, top_k, score_threshold)
        )
    
    def count(self) -> int:
        """Return the number of documents in the collection."""
        info = self._client.get_collection(self._collection_name)
        return info.points_count
    
    async def count_async(self) -> int:
        """Return the number of documents in the collection (async)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(get_qdrant_executor(), self.count)
    
    def delete_collection(self) -> None:
        """Delete and recreate the collection (clears all documents)."""
        try:
            self._client.delete_collection(self._collection_name)
            logger.info(f"[{self.watermark}] Deleted collection: {self._collection_name}")
            # Recreate empty collection so system keeps working
            self._ensure_collection()
            logger.info(f"[{self.watermark}] Recreated empty collection: {self._collection_name}")
        except Exception as e:
            logger.warning(f"[{self.watermark}] Could not delete collection: {e}")
    
    async def delete_collection_async(self) -> None:
        """Delete and recreate the collection (async)."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(get_qdrant_executor(), self.delete_collection)
