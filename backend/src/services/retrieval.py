"""
Retrieval Service - Phase 3 (Async Optimized)

Hybrid retrieval combining vector search and keyword search (BM25).
Fully async with concurrent search operations.

Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
"""
from dataclasses import dataclass
from typing import Any
from concurrent.futures import ThreadPoolExecutor
import asyncio
import logging

from rank_bm25 import BM25Okapi

from src.core.config import PROJECT_CONTEXT_ID
from src.services.embeddings import EmbeddingService
from src.services.vector_store import VectorStoreService, StoredDocument

logger = logging.getLogger(__name__)

# Thread pool for BM25 operations (CPU-bound)
_bm25_executor: ThreadPoolExecutor | None = None

def get_bm25_executor() -> ThreadPoolExecutor:
    """Get or create a thread pool for BM25 operations."""
    global _bm25_executor
    if _bm25_executor is None:
        _bm25_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="bm25")
    return _bm25_executor


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class RetrievalResult:
    """
    A document retrieved with relevance scoring.
    
    Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
    """
    id: str
    text: str
    score: float
    metadata: dict[str, Any]
    retrieval_method: str  # 'vector', 'keyword', or 'hybrid'
    watermark: str = PROJECT_CONTEXT_ID


# =============================================================================
# Retrieval Service (Async Optimized)
# =============================================================================

class RetrievalService:
    """
    Service for hybrid document retrieval.
    
    Combines:
    - Vector similarity search (semantic understanding)
    - BM25 keyword search (exact term matching)
    
    Async features:
    - Concurrent vector + keyword search
    - Non-blocking embedding and search operations
    
    Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
    """
    
    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: VectorStoreService,
        watermark: str = PROJECT_CONTEXT_ID
    ):
        """
        Initialize retrieval service.
        
        Args:
            embedding_service: Service for generating query embeddings
            vector_store: Service for vector similarity search
            watermark: Project watermark identifier
        """
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.watermark = watermark
        
        # BM25 index (built lazily from vector store contents)
        self._bm25_corpus: list[str] = []
        self._bm25_index: BM25Okapi | None = None
        self._bm25_docs: list[StoredDocument] = []
        
        logger.info(f"[{self.watermark}] RetrievalService initialized")
    
    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        use_keyword_search: bool = False,
        score_threshold: float | None = None
    ) -> list[RetrievalResult]:
        """
        Retrieve relevant documents for a query (sync).
        
        Args:
            query: User query text
            top_k: Number of results to return
            use_keyword_search: Enable hybrid keyword search
            score_threshold: Minimum score threshold
            
        Returns:
            List of RetrievalResult objects sorted by relevance
        """
        if not query or not query.strip():
            return []
        
        # Vector search
        query_vector = self.embedding_service.embed(query)
        vector_results = self.vector_store.search(
            query_vector,
            top_k=top_k,
            score_threshold=score_threshold
        )
        
        results = self._convert_to_retrieval_results(vector_results, "vector")
        
        # Optional: Combine with keyword search
        if use_keyword_search:
            keyword_results = self._keyword_search(query, top_k)
            results = self._merge_results(results, keyword_results, top_k)
        
        logger.debug(f"[{self.watermark}] Retrieved {len(results)} results for query")
        return results
    
    async def retrieve_async(
        self,
        query: str,
        top_k: int = 5,
        use_keyword_search: bool = False,
        score_threshold: float | None = None
    ) -> list[RetrievalResult]:
        """
        Retrieve relevant documents for a query (async).
        
        Uses concurrent execution for vector + keyword search.
        
        Args:
            query: User query text
            top_k: Number of results to return
            use_keyword_search: Enable hybrid keyword search
            score_threshold: Minimum score threshold
            
        Returns:
            List of RetrievalResult objects sorted by relevance
        """
        if not query or not query.strip():
            return []
        
        # Embed query async
        query_vector = await self.embedding_service.embed_async(query)
        
        if use_keyword_search:
            # Run vector and keyword search concurrently
            vector_task = self.vector_store.search_async(
                query_vector,
                top_k=top_k,
                score_threshold=score_threshold
            )
            keyword_task = self._keyword_search_async(query, top_k)
            
            vector_results, keyword_results = await asyncio.gather(
                vector_task, keyword_task
            )
            
            results = self._convert_to_retrieval_results(vector_results, "vector")
            results = self._merge_results(results, keyword_results, top_k)
        else:
            # Just vector search
            vector_results = await self.vector_store.search_async(
                query_vector,
                top_k=top_k,
                score_threshold=score_threshold
            )
            results = self._convert_to_retrieval_results(vector_results, "vector")
        
        logger.debug(f"[{self.watermark}] Async retrieved {len(results)} results for query")
        return results
    
    def _convert_to_retrieval_results(
        self,
        docs: list[StoredDocument],
        method: str
    ) -> list[RetrievalResult]:
        """Convert StoredDocument to RetrievalResult."""
        return [
            RetrievalResult(
                id=doc.id,
                text=doc.text,
                score=doc.score,
                metadata=doc.metadata,
                retrieval_method=method,
                watermark=self.watermark
            )
            for doc in docs
        ]
    
    def _keyword_search(self, query: str, top_k: int) -> list[RetrievalResult]:
        """
        Perform BM25 keyword search (sync).
        
        Builds index lazily from vector store if needed.
        """
        # Build BM25 index if not exists
        if self._bm25_index is None:
            self._build_bm25_index()
        
        if not self._bm25_corpus:
            return []
        
        # Tokenize query
        query_tokens = query.lower().split()
        
        # Get BM25 scores
        scores = self._bm25_index.get_scores(query_tokens)
        
        # Get top-k indices
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                doc = self._bm25_docs[idx]
                results.append(RetrievalResult(
                    id=doc.id,
                    text=doc.text,
                    score=float(scores[idx]),
                    metadata=doc.metadata,
                    retrieval_method="keyword",
                    watermark=self.watermark
                ))
        
        return results
    
    async def _keyword_search_async(self, query: str, top_k: int) -> list[RetrievalResult]:
        """
        Perform BM25 keyword search (async).
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            get_bm25_executor(),
            lambda: self._keyword_search(query, top_k)
        )
    
    def _build_bm25_index(self) -> None:
        """Build BM25 index from vector store contents."""
        # Get all documents from vector store
        # Note: This is a simplified approach - in production, you'd want pagination
        all_docs = self.vector_store.search(
            self.embedding_service.embed("document"),  # Dummy query to get all
            top_k=1000,
            score_threshold=0.0
        )
        
        self._bm25_docs = all_docs
        self._bm25_corpus = [doc.text.lower().split() for doc in all_docs]
        
        if self._bm25_corpus:
            self._bm25_index = BM25Okapi(self._bm25_corpus)
            logger.info(f"[{self.watermark}] Built BM25 index with {len(self._bm25_corpus)} documents")
    
    def _merge_results(
        self,
        vector_results: list[RetrievalResult],
        keyword_results: list[RetrievalResult],
        top_k: int,
        k: int = 60  # RRF constant
    ) -> list[RetrievalResult]:
        """
        Merge vector and keyword results using Reciprocal Rank Fusion (RRF).
        
        RRF Score = sum(1 / (k + rank)) for each result list
        This properly combines rankings from different retrieval methods.
        """
        # Build RRF scores
        rrf_scores: dict[str, float] = {}
        result_map: dict[str, RetrievalResult] = {}
        
        # Score from vector results (rank-based)
        for rank, r in enumerate(vector_results):
            rrf_scores[r.id] = rrf_scores.get(r.id, 0) + 1.0 / (k + rank + 1)
            result_map[r.id] = r
        
        # Score from keyword results (rank-based)
        for rank, r in enumerate(keyword_results):
            rrf_scores[r.id] = rrf_scores.get(r.id, 0) + 1.0 / (k + rank + 1)
            if r.id not in result_map:
                result_map[r.id] = r
        
        # Sort by RRF score descending
        sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
        
        # Build final results
        merged = []
        for doc_id in sorted_ids[:top_k]:
            result = result_map[doc_id]
            result.retrieval_method = "hybrid"
            result.score = rrf_scores[doc_id]  # Replace with RRF score for consistency
            merged.append(result)
        
        return merged
    
    def invalidate_bm25_index(self) -> None:
        """Invalidate BM25 index (call after adding new documents)."""
        self._bm25_index = None
        self._bm25_corpus = []
        self._bm25_docs = []
        logger.debug(f"[{self.watermark}] BM25 index invalidated")
