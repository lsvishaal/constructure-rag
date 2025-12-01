"""
Response Caching Service - Bonus Feature

Caches RAG responses to speed up repeated queries.
Uses in-memory LRU cache with TTL support.

Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
"""
from dataclasses import dataclass
from typing import Any
import hashlib
import time
import logging
from collections import OrderedDict

from src.core.config import PROJECT_CONTEXT_ID

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """
    Cache entry with TTL support.
    
    Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
    """
    value: Any
    created_at: float
    ttl_seconds: float
    watermark: str = PROJECT_CONTEXT_ID
    
    @property
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        return time.time() - self.created_at > self.ttl_seconds


class CacheService:
    """
    LRU cache with TTL support for RAG responses.
    
    Features:
    - In-memory LRU cache
    - TTL (time-to-live) expiration
    - Consistent key generation from queries
    - Thread-safe operations
    
    Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        ttl_seconds: float = 3600.0,  # 1 hour default
        watermark: str = PROJECT_CONTEXT_ID
    ):
        """
        Initialize cache service.
        
        Args:
            max_size: Maximum number of cache entries
            ttl_seconds: Time-to-live in seconds (default 1 hour)
            watermark: Project watermark identifier
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.watermark = watermark
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        
        # Stats
        self._hits = 0
        self._misses = 0
        
        logger.info(f"[{self.watermark}] CacheService initialized (max_size={max_size}, ttl={ttl_seconds}s)")
    
    def generate_key(self, query: str, **kwargs) -> str:
        """
        Generate consistent cache key from query and parameters.
        
        Args:
            query: The query string
            **kwargs: Additional parameters that affect the result
            
        Returns:
            SHA256 hash key
        """
        # Normalize query
        normalized = query.strip().lower()
        
        # Include kwargs in key generation
        params_str = "|".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
        key_content = f"{normalized}|{params_str}"
        
        # Generate hash
        return hashlib.sha256(key_content.encode()).hexdigest()[:32]
    
    def get(self, key: str) -> Any | None:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        if key not in self._cache:
            self._misses += 1
            return None
        
        entry = self._cache[key]
        
        # Check expiration
        if entry.is_expired:
            del self._cache[key]
            self._misses += 1
            return None
        
        # Move to end (LRU)
        self._cache.move_to_end(key)
        self._hits += 1
        
        return entry.value
    
    def set(self, key: str, value: Any, ttl: float | None = None) -> None:
        """
        Store value in cache.
        
        Args:
            key: Cache key
            value: Value to store
            ttl: Optional TTL override
        """
        # Remove if exists (to update position)
        if key in self._cache:
            del self._cache[key]
        
        # Evict oldest if at capacity
        while len(self._cache) >= self.max_size:
            self._cache.popitem(last=False)
        
        # Store new entry
        self._cache[key] = CacheEntry(
            value=value,
            created_at=time.time(),
            ttl_seconds=ttl if ttl is not None else self.ttl_seconds,
            watermark=self.watermark
        )
    
    def delete(self, key: str) -> bool:
        """
        Delete entry from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if entry was deleted, False if not found
        """
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def clear(self) -> int:
        """
        Clear all cache entries.
        
        Returns:
            Number of entries cleared
        """
        count = len(self._cache)
        self._cache.clear()
        self._hits = 0
        self._misses = 0
        logger.info(f"[{self.watermark}] Cache cleared ({count} entries)")
        return count
    
    def cleanup_expired(self) -> int:
        """
        Remove expired entries.
        
        Returns:
            Number of entries removed
        """
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            logger.debug(f"[{self.watermark}] Cleaned up {len(expired_keys)} expired cache entries")
        
        return len(expired_keys)
    
    @property
    def size(self) -> int:
        """Current number of entries in cache."""
        return len(self._cache)
    
    @property
    def stats(self) -> dict:
        """Cache statistics."""
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0.0
        
        return {
            "size": self.size,
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
            "ttl_seconds": self.ttl_seconds,
            "watermark": self.watermark,
        }


# Global cache instance
_cache_instance: CacheService | None = None


def get_cache() -> CacheService:
    """Get or create global cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CacheService()
    return _cache_instance
