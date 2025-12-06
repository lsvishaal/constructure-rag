"""
Embeddings Service - Phase 2 (Async Optimized)

Text embedding generation using fastembed (lightweight ONNX-based).
Fully async with concurrent processing support.

Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
"""
from dataclasses import dataclass
from typing import Any
from concurrent.futures import ThreadPoolExecutor
import asyncio
import numpy as np
import logging

from fastembed import TextEmbedding

from src.core.config import PROJECT_CONTEXT_ID

logger = logging.getLogger(__name__)

# Global thread pool for CPU-bound embedding operations
_embedding_executor: ThreadPoolExecutor | None = None

def get_embedding_executor() -> ThreadPoolExecutor:
    """Get or create a thread pool for embedding operations."""
    global _embedding_executor
    if _embedding_executor is None:
        # Use 4 workers - embeddings are CPU-bound, too many threads = contention
        _embedding_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="embed")
    return _embedding_executor


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class EmbeddedChunk:
    """
    A chunk with its embedding vector.
    
    Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
    """
    text: str
    vector: np.ndarray
    metadata: dict[str, Any]
    watermark: str = PROJECT_CONTEXT_ID


# =============================================================================
# Embedding Service (Async Optimized)
# =============================================================================

class EmbeddingService:
    """
    Service for generating text embeddings using fastembed.
    
    Uses BAAI/bge-small-en-v1.5 model (384 dimensions).
    Lightweight, fast, ONNX-based - no PyTorch required.
    
    Optimized features:
    - Batch processing with large batch sizes
    - Async wrappers for non-blocking operation
    - Thread pool for CPU-bound work
    
    Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
    """
    
    # Default model: BGE-small-en-v1.5 (384 dim, good quality/speed tradeoff)
    DEFAULT_MODEL = "BAAI/bge-small-en-v1.5"
    DEFAULT_DIMENSION = 384
    # Optimal batch size for ONNX inference (larger = faster but more memory)
    OPTIMAL_BATCH_SIZE = 64
    
    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        watermark: str = PROJECT_CONTEXT_ID
    ):
        """
        Initialize embedding service.
        
        Args:
            model_name: Fastembed model name
            watermark: Project watermark identifier
        """
        self._model_name = model_name
        self.watermark = watermark
        self._dimension = self.DEFAULT_DIMENSION
        
        # Lazy-load model on first use
        self._model: TextEmbedding | None = None
        
        logger.info(f"[{self.watermark}] EmbeddingService initialized with model: {model_name}")
    
    @property
    def model(self) -> TextEmbedding:
        """Lazy-load the embedding model with optimized settings."""
        if self._model is None:
            logger.info(f"[{self.watermark}] Loading embedding model: {self._model_name}")
            # Use parallel processing for faster embedding
            self._model = TextEmbedding(
                model_name=self._model_name,
                threads=None,  # Use all available CPU threads
            )
        return self._model
    
    @property
    def dimension(self) -> int:
        """Return embedding dimension."""
        return self._dimension
    
    @property
    def model_name(self) -> str:
        """Return model name."""
        return self._model_name
    
    def embed(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text (sync).
        
        Args:
            text: Text to embed
            
        Returns:
            numpy array of shape (384,)
        """
        # fastembed returns a generator, take first result
        embeddings = list(self.model.embed([text]))
        vector = np.array(embeddings[0], dtype=np.float32)
        
        logger.debug(f"[{self.watermark}] Embedded text of length {len(text)}")
        return vector
    
    async def embed_async(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text (async).
        
        Runs embedding in thread pool to avoid blocking event loop.
        
        Args:
            text: Text to embed
            
        Returns:
            numpy array of shape (384,)
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(get_embedding_executor(), self.embed, text)
    
    def embed_batch(self, texts: list[str], batch_size: int | None = None) -> list[np.ndarray]:
        """
        Generate embeddings for multiple texts with optimized batching (sync).
        
        Args:
            texts: List of texts to embed
            batch_size: Optional batch size (default: OPTIMAL_BATCH_SIZE)
            
        Returns:
            List of numpy arrays
        """
        if not texts:
            return []
        
        batch_size = batch_size or self.OPTIMAL_BATCH_SIZE
        
        # fastembed's embed() is already optimized for batching
        # Pass batch_size hint for better memory management
        embeddings = list(self.model.embed(texts, batch_size=batch_size))
        vectors = [np.array(emb, dtype=np.float32) for emb in embeddings]
        
        logger.debug(f"[{self.watermark}] Embedded batch of {len(texts)} texts (batch_size={batch_size})")
        return vectors
    
    async def embed_batch_async(self, texts: list[str], batch_size: int | None = None) -> list[np.ndarray]:
        """
        Generate embeddings for multiple texts (async).
        
        Runs batch embedding in thread pool to avoid blocking event loop.
        
        Args:
            texts: List of texts to embed
            batch_size: Optional batch size (default: OPTIMAL_BATCH_SIZE)
            
        Returns:
            List of numpy arrays
        """
        if not texts:
            return []
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            get_embedding_executor(),
            lambda: self.embed_batch(texts, batch_size)
        )
    
    def embed_chunk(self, chunk: dict[str, Any]) -> EmbeddedChunk:
        """
        Embed a single chunk and return EmbeddedChunk.
        
        Args:
            chunk: Dict with 'text' and metadata fields
            
        Returns:
            EmbeddedChunk with vector and metadata
        """
        text = chunk["text"]
        vector = self.embed(text)
        
        # Build metadata (exclude text, keep everything else)
        metadata = {k: v for k, v in chunk.items() if k != "text"}
        
        return EmbeddedChunk(
            text=text,
            vector=vector,
            metadata=metadata,
            watermark=self.watermark
        )
    
    def embed_chunks(self, chunks: list[dict[str, Any]]) -> list[EmbeddedChunk]:
        """
        Embed multiple chunks efficiently using batch embedding.
        
        Args:
            chunks: List of chunk dicts
            
        Returns:
            List of EmbeddedChunk objects
        """
        texts = [chunk["text"] for chunk in chunks]
        vectors = self.embed_batch(texts)
        
        results = []
        for chunk, vector in zip(chunks, vectors):
            metadata = {k: v for k, v in chunk.items() if k != "text"}
            results.append(EmbeddedChunk(
                text=chunk["text"],
                vector=vector,
                metadata=metadata,
                watermark=self.watermark
            ))
        
        logger.info(f"[{self.watermark}] Embedded {len(results)} chunks")
        return results
    
    async def embed_chunks_async(self, chunks: list[dict[str, Any]]) -> list[EmbeddedChunk]:
        """
        Embed multiple chunks efficiently (async).
        
        Args:
            chunks: List of chunk dicts
            
        Returns:
            List of EmbeddedChunk objects
        """
        texts = [chunk["text"] for chunk in chunks]
        vectors = await self.embed_batch_async(texts)
        
        results = []
        for chunk, vector in zip(chunks, vectors):
            metadata = {k: v for k, v in chunk.items() if k != "text"}
            results.append(EmbeddedChunk(
                text=chunk["text"],
                vector=vector,
                metadata=metadata,
                watermark=self.watermark
            ))
        
        logger.info(f"[{self.watermark}] Async embedded {len(results)} chunks")
        return results
