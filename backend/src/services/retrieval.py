"""
Retrieval Service - Phase 3

Hybrid retrieval combining vector search and keyword search (BM25).
Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
"""
from dataclasses import dataclass
from typing import Any
import logging

from rank_bm25 import BM25Okapi

from src.core.config import PROJECT_CONTEXT_ID
from src.services.embeddings import EmbeddingService
from src.services.vector_store import VectorStoreService, StoredDocument

logger = logging.getLogger(__name__)


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
# Retrieval Service
# =============================================================================

class RetrievalService:
    """
    Service for hybrid document retrieval.
    
    Combines:
    - Vector similarity search (semantic understanding)
    - BM25 keyword search (exact term matching)
    
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
        Retrieve relevant documents for a query.
        
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
        Perform BM25 keyword search.
        
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
        top_k: int
    ) -> list[RetrievalResult]:
        """
        Merge vector and keyword results using reciprocal rank fusion.
        """
        # Simple merge: deduplicate and re-rank
        seen_ids = set()
        merged = []
        
        # Interleave results, prioritizing vector search
        for vr, kr in zip(vector_results, keyword_results + [None] * len(vector_results)):
            if vr.id not in seen_ids:
                vr.retrieval_method = "hybrid"
                merged.append(vr)
                seen_ids.add(vr.id)
            
            if kr and kr.id not in seen_ids:
                kr.retrieval_method = "hybrid"
                merged.append(kr)
                seen_ids.add(kr.id)
        
        # Add any remaining
        for r in vector_results + keyword_results:
            if r.id not in seen_ids:
                r.retrieval_method = "hybrid"
                merged.append(r)
                seen_ids.add(r.id)
        
        return merged[:top_k]
    
    def invalidate_bm25_index(self) -> None:
        """Invalidate BM25 index (call after adding new documents)."""
        self._bm25_index = None
        self._bm25_corpus = []
        self._bm25_docs = []
        logger.debug(f"[{self.watermark}] BM25 index invalidated")
