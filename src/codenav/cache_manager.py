#!/usr/bin/env python3
"""
Hybrid Cache Manager for Code Graph MCP

Implements multi-tiered caching strategy:
L1: In-Memory LRU (fast access)
L2: Redis (persistent, shared)
L3: Source files (fallback)

This module provides a unified interface for caching that transparently
handles both memory and Redis backends with intelligent fallback.
"""

import asyncio
import logging
import time
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

from .redis_cache import RedisCacheBackend, RedisConfig, FileMetadata
from .universal_graph import UniversalNode, UniversalRelationship

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CacheStrategy:
    """Cache strategy configuration."""
    MEMORY_ONLY = "memory_only"
    REDIS_ONLY = "redis_only" 
    HYBRID = "hybrid"            # Memory + Redis
    REDIS_FALLBACK = "redis_fallback"  # Try Redis, fallback to memory


class HybridCacheManager:
    """
    Multi-tiered cache manager that combines in-memory LRU caches
    with Redis for persistence and sharing across instances.
    """
    
    def __init__(
        self,
        redis_config: Optional[RedisConfig] = None,
        strategy: str = CacheStrategy.HYBRID,
        enable_metrics: bool = True
    ):
        self.redis_config = redis_config or RedisConfig()
        self.strategy = strategy
        self.enable_metrics = enable_metrics
        
        # Cache backends
        self.redis_backend: Optional[RedisCacheBackend] = None
        self.memory_cache: Dict[str, Any] = {}
        
        # Cache statistics
        self.stats = {
            "hits": {"memory": 0, "redis": 0, "miss": 0},
            "operations": {"get": 0, "set": 0, "delete": 0},
            "errors": {"redis": 0, "serialization": 0},
            "timing": {"redis_get": [], "redis_set": [], "total": []}
        }
        
        # Connection state
        self._redis_available = False
        self._initialization_lock = asyncio.Lock()
        
    async def initialize(self) -> bool:
        """Initialize cache backends."""
        async with self._initialization_lock:
            if self.strategy in [CacheStrategy.MEMORY_ONLY]:
                logger.info("Cache manager initialized in memory-only mode")
                return True
            
            # Initialize Redis backend
            if not self.redis_backend:
                self.redis_backend = RedisCacheBackend(self.redis_config)
            
            # Test Redis connection
            self._redis_available = await self.redis_backend.connect()
            
            if self._redis_available:
                logger.info(f"Hybrid cache manager initialized with Redis backend")
                return True
            elif self.strategy == CacheStrategy.REDIS_FALLBACK:
                logger.warning("Redis unavailable, falling back to memory-only mode")
                self.strategy = CacheStrategy.MEMORY_ONLY
                return True
            else:
                logger.error("Redis backend required but unavailable")
                return False
    
    async def close(self):
        """Close cache backends."""
        if self.redis_backend:
            await self.redis_backend.disconnect()
        self.memory_cache.clear()
        logger.info("Cache manager closed")
    
    def _record_stat(self, category: str, subcategory: str, value: Union[int, float] = 1):
        """Record cache statistics."""
        if not self.enable_metrics:
            return
            
        if category in self.stats:
            if isinstance(self.stats[category], dict) and subcategory in self.stats[category]:
                if isinstance(self.stats[category][subcategory], list):
                    self.stats[category][subcategory].append(value)
                    # Keep only last 100 timing measurements
                    if len(self.stats[category][subcategory]) > 100:
                        self.stats[category][subcategory] = self.stats[category][subcategory][-100:]
                else:
                    self.stats[category][subcategory] += value
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache with L1 → L2 fallback."""
        start_time = time.time()
        self._record_stat("operations", "get")
        
        try:
            # L1: Memory cache
            if key in self.memory_cache:
                self._record_stat("hits", "memory")
                return self.memory_cache[key]
            
            # L2: Redis cache (if available and strategy allows)
            if self._should_use_redis():
                redis_start = time.time()
                
                value = await self.redis_backend.get_analysis_result(key)
                redis_time = time.time() - redis_start
                self._record_stat("timing", "redis_get", redis_time)
                
                if value is not None:
                    self._record_stat("hits", "redis")
                    # Cache in L1 for future hits
                    self.memory_cache[key] = value
                    return value
            
            # Cache miss
            self._record_stat("hits", "miss")
            return default
            
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {e}")
            self._record_stat("errors", "redis" if "redis" in str(e).lower() else "serialization")
            return default
        
        finally:
            total_time = time.time() - start_time
            self._record_stat("timing", "total", total_time)
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache (both L1 and L2)."""
        self._record_stat("operations", "set")
        
        success = True
        
        try:
            # L1: Always cache in memory
            self.memory_cache[key] = value
            
            # L2: Cache in Redis if available and strategy allows
            if self._should_use_redis():
                redis_start = time.time()
                
                redis_success = await self.redis_backend.set_analysis_result(key, value, ttl)
                redis_time = time.time() - redis_start
                self._record_stat("timing", "redis_set", redis_time)
                
                if not redis_success:
                    logger.warning(f"Failed to cache key {key} in Redis")
                    self._record_stat("errors", "redis")
                    success = False
            
            return success
            
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {e}")
            self._record_stat("errors", "redis" if "redis" in str(e).lower() else "serialization")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from all cache levels."""
        self._record_stat("operations", "delete")
        
        success = True
        
        try:
            # L1: Remove from memory
            self.memory_cache.pop(key, None)
            
            # L2: Remove from Redis
            if self._should_use_redis():
                # Delete from Redis
                if self.redis_backend.redis:
                    redis_key = f"{self.redis_config.prefix}:{self.redis_config.analysis_prefix}:{key}"
                    deleted = await self.redis_backend.redis.delete(redis_key)
                    if deleted == 0:
                        success = False
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {e}")
            return False
    
    def _should_use_redis(self) -> bool:
        """Check if Redis should be used based on strategy and availability."""
        return (
            self._redis_available and 
            self.strategy in [CacheStrategy.REDIS_ONLY, CacheStrategy.HYBRID] and
            self.redis_backend is not None
        )
    
    # File-specific caching methods
    
    async def is_file_cached(self, file_path: Path) -> bool:
        """Check if file analysis is cached and valid."""
        if not self._should_use_redis():
            return False
        
        return await self.redis_backend.is_file_cached_and_valid(file_path)
    
    async def get_file_nodes(self, file_path: str) -> Optional[List[Dict]]:
        """Get cached nodes for a file."""
        if not self._should_use_redis():
            return None
        
        return await self.redis_backend.get_file_nodes(file_path)
    
    async def set_file_nodes(self, file_path: str, nodes: List[UniversalNode]) -> bool:
        """Cache nodes for a file."""
        if not self._should_use_redis():
            return False
        
        # Also cache file metadata
        path_obj = Path(file_path)
        if path_obj.exists():
            metadata = FileMetadata.from_path(path_obj)
            await self.redis_backend.set_file_metadata(metadata)
        
        return await self.redis_backend.set_file_nodes(file_path, nodes)
    
    async def get_file_relationships(self, file_path: str) -> Optional[List[Dict]]:
        """Get cached relationships for a file."""
        if not self._should_use_redis():
            return None
        
        return await self.redis_backend.get_file_relationships(file_path)
    
    async def set_file_relationships(self, file_path: str, relationships: List[UniversalRelationship]) -> bool:
        """Cache relationships for a file."""
        if not self._should_use_redis():
            return False
        
        return await self.redis_backend.set_file_relationships(file_path, relationships)
    
    async def invalidate_file(self, file_path: str) -> int:
        """Invalidate all cached data for a file."""
        # Clear from memory cache (remove any keys containing the file path)
        memory_deletions = 0
        keys_to_delete = [k for k in self.memory_cache.keys() if file_path in k]
        for key in keys_to_delete:
            del self.memory_cache[key]
            memory_deletions += 1
        
        # Clear from Redis
        redis_deletions = 0
        if self._should_use_redis():
            redis_deletions = await self.redis_backend.invalidate_file(file_path)
        
        total_deletions = memory_deletions + redis_deletions
        logger.info(f"Invalidated {total_deletions} cache entries for {file_path}")
        return total_deletions
    
    async def clear_all(self) -> bool:
        """Clear all cache data."""
        # Clear memory
        self.memory_cache.clear()
        
        # Clear Redis
        if self._should_use_redis():
            await self.redis_backend.clear_all_cache()
        
        logger.info("All cache data cleared")
        return True
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        stats = {
            "strategy": self.strategy,
            "redis_available": self._redis_available,
            "memory_keys": len(self.memory_cache),
            "stats": self.stats.copy()
        }
        
        # Add Redis-specific stats
        if self._should_use_redis():
            redis_stats = await self.redis_backend.get_stats()
            stats["redis"] = redis_stats
        
        # Calculate hit rates
        total_hits = sum(self.stats["hits"].values())
        if total_hits > 0:
            stats["hit_rates"] = {
                category: (count / total_hits * 100)
                for category, count in self.stats["hits"].items()
            }
        
        # Calculate average timing
        for timing_type, times in self.stats["timing"].items():
            if times:
                stats["avg_timing"] = stats.get("avg_timing", {})
                stats["avg_timing"][timing_type] = sum(times) / len(times)
        
        return stats


# Decorator for automatic caching
def cached_method(
    ttl: Optional[int] = None,
    key_generator: Optional[Callable] = None,
    cache_manager_attr: str = "cache_manager"
):
    """
    Decorator for automatic method result caching.
    
    Args:
        ttl: Time to live in seconds
        key_generator: Function to generate cache key from args
        cache_manager_attr: Attribute name for the cache manager
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Get cache manager from instance
            cache_manager: HybridCacheManager = getattr(self, cache_manager_attr, None)
            if not cache_manager:
                # No cache manager, execute directly
                return await func(self, *args, **kwargs)
            
            # Generate cache key
            if key_generator:
                cache_key = key_generator(self, *args, **kwargs)
            else:
                # Default key generation
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(self, *args, **kwargs)
            await cache_manager.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator