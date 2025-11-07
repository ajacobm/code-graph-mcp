#!/usr/bin/env python3
"""
Redis Cache Backend for Code Graph MCP

Provides distributed, persistent caching with incremental updates
for code analysis results and graph data.

This module implements a hybrid caching strategy:
L1 (Memory) → L2 (Redis) → L3 (Source Files)
"""

import asyncio
import hashlib
import json
import logging
import pickle
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import redis.asyncio as redis
from redis.asyncio import Redis

from .universal_graph import UniversalNode, UniversalRelationship, NodeType, RelationshipType

logger = logging.getLogger(__name__)


def serialize_node(node: UniversalNode) -> Dict[str, Any]:
    """Convert UniversalNode to serializable dict, handling Enums."""
    data = asdict(node)
    # Convert Enum to string
    if 'node_type' in data and isinstance(data['node_type'], NodeType):
        data['node_type'] = data['node_type'].value
    return data


def serialize_relationship(rel: UniversalRelationship) -> Dict[str, Any]:
    """Convert UniversalRelationship to serializable dict, handling Enums."""
    data = asdict(rel)
    # Convert Enum to string
    if 'relationship_type' in data and isinstance(data['relationship_type'], RelationshipType):
        data['relationship_type'] = data['relationship_type'].value
    return data


@dataclass
class RedisConfig:
    """Configuration for Redis cache backend."""
    url: str = "redis://redis:6379"
    db: int = 0
    password: Optional[str] = None
    socket_timeout: float = 5.0
    socket_connect_timeout: float = 5.0
    health_check_interval: int = 30
    
    # Cache settings
    default_ttl: int = 86400 * 7  # 1 week
    max_memory_usage: str = "1gb"
    eviction_policy: str = "allkeys-lru"
    
    # Key prefixes
    prefix: str = "code_graph"
    nodes_prefix: str = "nodes"
    edges_prefix: str = "edges"
    analysis_prefix: str = "analysis"
    metadata_prefix: str = "meta"
    
    # Serialization
    compression: bool = True
    serialization_format: str = "msgpack"  # or "pickle" or "json"


@dataclass 
class FileMetadata:
    """File metadata for cache validation."""
    file_path: str
    modification_time: float
    size: int
    content_hash: str
    
    @classmethod
    def from_path(cls, path: Path) -> "FileMetadata":
        """Create metadata from file path."""
        stat = path.stat()
        with open(path, 'rb') as f:
            content_hash = hashlib.sha256(f.read()).hexdigest()[:16]
        
        return cls(
            file_path=str(path),
            modification_time=stat.st_mtime,
            size=stat.st_size,
            content_hash=content_hash
        )


class RedisSerializer:
    """Handles serialization/deserialization for Redis storage."""
    
    def __init__(self, format_type: str = "msgpack", compression: bool = True):
        self.format_type = format_type
        self.compression = compression
        
        if format_type == "msgpack":
            try:
                import msgpack
                self.msgpack = msgpack
            except ImportError:
                logger.warning("msgpack not available, falling back to pickle")
                self.format_type = "pickle"
    
    def serialize(self, data: Any) -> bytes:
        """Serialize data for Redis storage."""
        try:
            # Convert problematic types to serializable formats
            data = self._make_serializable(data)
            
            if self.format_type == "msgpack":
                if isinstance(data, (UniversalNode, UniversalRelationship)):
                    data = asdict(data)
                serialized = self.msgpack.packb(data, use_bin_type=True)
            elif self.format_type == "json":
                if isinstance(data, (UniversalNode, UniversalRelationship)):
                    data = asdict(data)
                serialized = json.dumps(data, default=str).encode('utf-8')
            else:  # pickle
                serialized = pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)
            
            if self.compression:
                import gzip
                serialized = gzip.compress(serialized)
            
            return serialized
            
        except Exception as e:
            logger.error(f"Serialization error: {e}")
            raise
    
    def _make_serializable(self, obj: Any, _seen: Optional[set] = None) -> Any:
        """Convert non-serializable objects to serializable format."""
        if _seen is None:
            _seen = set()
        
        # Check for circular references
        obj_id = id(obj)
        if obj_id in _seen:
            # Return a placeholder for circular references
            return f"<circular_ref:{type(obj).__name__}>"
        
        if isinstance(obj, set):
            return list(obj)
        elif isinstance(obj, dict):
            _seen.add(obj_id)
            try:
                result = {k: self._make_serializable(v, _seen) for k, v in obj.items()}
            finally:
                _seen.discard(obj_id)
            return result
        elif isinstance(obj, (list, tuple)):
            _seen.add(obj_id)
            try:
                result = [self._make_serializable(item, _seen) for item in obj]
            finally:
                _seen.discard(obj_id)
            return result
        elif hasattr(obj, '__dict__'):
            _seen.add(obj_id)
            try:
                # Convert custom objects to dict representation
                if hasattr(obj, '_asdict'):  # namedtuple
                    return obj._asdict()
                else:
                    return {k: self._make_serializable(v, _seen) for k, v in obj.__dict__.items()}
            finally:
                _seen.discard(obj_id)
        else:
            return obj
    
    def deserialize(self, data: bytes) -> Any:
        """Deserialize data from Redis storage."""
        try:
            if self.compression:
                import gzip
                data = gzip.decompress(data)
            
            if self.format_type == "msgpack":
                return self.msgpack.unpackb(data, raw=False)
            elif self.format_type == "json":
                return json.loads(data.decode('utf-8'))
            else:  # pickle
                return pickle.loads(data)
                
        except Exception as e:
            logger.error(f"Deserialization error: {e}")
            raise


class RedisCacheBackend:
    """Redis-based cache backend for code graph data."""
    
    def __init__(self, config: RedisConfig):
        self.config = config
        self.serializer = RedisSerializer(
            config.serialization_format,
            config.compression
        )
        self.redis: Optional[Redis] = None
        self._connected = False
        self._connection_lock = asyncio.Lock()
    
    async def connect(self) -> bool:
        """Initialize Redis connection."""
        async with self._connection_lock:
            if self._connected:
                return True
                
            try:
                self.redis = redis.from_url(
                    self.config.url,
                    db=self.config.db,
                    password=self.config.password,
                    socket_timeout=self.config.socket_timeout,
                    socket_connect_timeout=self.config.socket_connect_timeout,
                    health_check_interval=self.config.health_check_interval,
                    decode_responses=False  # We handle our own serialization
                )
                
                # Test connection
                await self.redis.ping()
                
                # Configure Redis for optimal caching
                await self._configure_redis()
                
                self._connected = True
                logger.info("Redis cache backend connected successfully")
                return True
                
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self.redis = None
                self._connected = False
                return False
    
    async def disconnect(self):
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
            self.redis = None
            self._connected = False
            logger.info("Redis cache backend disconnected")
    
    async def _configure_redis(self):
        """Configure Redis for optimal caching performance."""
        try:
            # Set memory policy
            await self.redis.config_set("maxmemory-policy", self.config.eviction_policy)
            
            if self.config.max_memory_usage:
                await self.redis.config_set("maxmemory", self.config.max_memory_usage)
            
            logger.info("Redis cache configuration applied")
            
        except Exception as e:
            logger.warning(f"Could not configure Redis settings: {e}")
    
    def _make_key(self, *parts: str) -> str:
        """Create a Redis key with consistent formatting."""
        return f"{self.config.prefix}:{':'.join(parts)}"
    
    async def is_healthy(self) -> bool:
        """Check if Redis backend is healthy."""
        try:
            if not self._connected:
                return False
            await self.redis.ping()
            return True
        except Exception:
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get Redis cache statistics."""
        if not self._connected:
            return {"status": "disconnected"}
        
        try:
            info = await self.redis.info()
            
            # Count keys by type
            pattern = f"{self.config.prefix}:*"
            keys = await self.redis.keys(pattern)
            
            stats = {
                "status": "connected",
                "redis_version": info.get("redis_version"),
                "used_memory": info.get("used_memory_human"),
                "total_keys": len(keys),
                "memory_usage": info.get("used_memory"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "connected_clients": info.get("connected_clients"),
            }
            
            # Calculate hit rate
            hits = stats["keyspace_hits"]
            misses = stats["keyspace_misses"] 
            total = hits + misses
            stats["hit_rate"] = (hits / total * 100) if total > 0 else 0
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting Redis stats: {e}")
            return {"status": "error", "error": str(e)}
    
    # File-level caching methods
    
    async def get_file_metadata(self, file_path: str) -> Optional[FileMetadata]:
        """Get cached file metadata."""
        if not self._connected:
            return None
        
        try:
            key = self._make_key(self.config.metadata_prefix, file_path)
            data = await self.redis.get(key)
            
            if data:
                meta_dict = self.serializer.deserialize(data)
                return FileMetadata(**meta_dict)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting file metadata for {file_path}: {e}")
            return None
    
    async def set_file_metadata(self, metadata: FileMetadata, ttl: Optional[int] = None) -> bool:
        """Cache file metadata."""
        if not self._connected:
            return False
        
        try:
            key = self._make_key(self.config.metadata_prefix, metadata.file_path)
            data = self.serializer.serialize(asdict(metadata))
            
            ttl = ttl or self.config.default_ttl
            await self.redis.setex(key, ttl, data)
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting file metadata for {metadata.file_path}: {e}")
            return False
    
    async def is_file_cached_and_valid(self, file_path: Path) -> bool:
        """Check if file is cached and cache is still valid."""
        try:
            # Get cached metadata
            cached_meta = await self.get_file_metadata(str(file_path))
            if not cached_meta:
                return False
            
            # Get current file metadata
            if not file_path.exists():
                return False
            
            current_meta = FileMetadata.from_path(file_path)
            
            # Compare metadata for cache validity
            return (
                cached_meta.modification_time == current_meta.modification_time and
                cached_meta.size == current_meta.size and
                cached_meta.content_hash == current_meta.content_hash
            )
            
        except Exception as e:
            logger.error(f"Error checking cache validity for {file_path}: {e}")
            return False
    
    async def get_file_nodes(self, file_path: str) -> Optional[List[Dict]]:
        """Get cached nodes for a file."""
        if not self._connected:
            return None
        
        try:
            key = self._make_key(self.config.nodes_prefix, file_path)
            data = await self.redis.get(key)
            
            if data:
                return self.serializer.deserialize(data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached nodes for {file_path}: {e}")
            return None
    
    async def set_file_nodes(self, file_path: str, nodes: List[UniversalNode], ttl: Optional[int] = None) -> bool:
        """Cache nodes for a file."""
        if not self._connected:
            return False
        
        try:
            key = self._make_key(self.config.nodes_prefix, file_path)
            
            # Convert nodes to serializable format
            serializable_nodes = [serialize_node(node) for node in nodes]
            data = self.serializer.serialize(serializable_nodes)
            
            ttl = ttl or self.config.default_ttl
            await self.redis.setex(key, ttl, data)
            
            return True
            
        except Exception as e:
            logger.error(f"Error caching nodes for {file_path}: {e}")
            return False
    
    async def get_file_relationships(self, file_path: str) -> Optional[List[Dict]]:
        """Get cached relationships for a file."""
        if not self._connected:
            return None
        
        try:
            key = self._make_key(self.config.edges_prefix, file_path)
            data = await self.redis.get(key)
            
            if data:
                return self.serializer.deserialize(data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached relationships for {file_path}: {e}")
            return None
    
    async def set_file_relationships(self, file_path: str, relationships: List[UniversalRelationship], ttl: Optional[int] = None) -> bool:
        """Cache relationships for a file."""
        if not self._connected:
            return False
        
        try:
            key = self._make_key(self.config.edges_prefix, file_path)
            
            # Convert relationships to serializable format
            serializable_rels = [serialize_relationship(rel) for rel in relationships]
            data = self.serializer.serialize(serializable_rels)
            
            ttl = ttl or self.config.default_ttl
            await self.redis.setex(key, ttl, data)
            
            return True
            
        except Exception as e:
            logger.error(f"Error caching relationships for {file_path}: {e}")
            return False
    
    # Analysis result caching
    
    async def get_analysis_result(self, cache_key: str) -> Optional[Any]:
        """Get cached analysis result."""
        if not self._connected:
            return None
        
        try:
            key = self._make_key(self.config.analysis_prefix, cache_key)
            data = await self.redis.get(key)
            
            if data:
                return self.serializer.deserialize(data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached analysis result for {cache_key}: {e}")
            return None
    
    async def set_analysis_result(self, cache_key: str, result: Any, ttl: Optional[int] = None) -> bool:
        """Cache analysis result."""
        if not self._connected:
            return False
        
        try:
            key = self._make_key(self.config.analysis_prefix, cache_key)
            data = self.serializer.serialize(result)
            
            ttl = ttl or self.config.default_ttl
            await self.redis.setex(key, ttl, data)
            
            return True
            
        except Exception as e:
            logger.error(f"Error caching analysis result for {cache_key}: {e}")
            return False
    
    # Bulk operations
    
    async def invalidate_file(self, file_path: str) -> int:
        """Invalidate all cached data for a specific file."""
        if not self._connected:
            return 0
        
        try:
            patterns = [
                f"{self.config.prefix}:{self.config.nodes_prefix}:{file_path}",
                f"{self.config.prefix}:{self.config.edges_prefix}:{file_path}",
                f"{self.config.prefix}:{self.config.metadata_prefix}:{file_path}",
                # Also invalidate any analysis results that might depend on this file
                f"{self.config.prefix}:{self.config.analysis_prefix}:*{file_path}*"
            ]
            
            deleted_count = 0
            for pattern in patterns:
                keys = await self.redis.keys(pattern)
                if keys:
                    deleted_count += await self.redis.delete(*keys)
            
            logger.info(f"Invalidated {deleted_count} cache entries for file: {file_path}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error invalidating cache for {file_path}: {e}")
            return 0
    
    async def invalidate_all_analysis(self) -> int:
        """Invalidate all cached analysis results (but keep parsed nodes/edges)."""
        if not self._connected:
            return 0
        
        try:
            pattern = f"{self.config.prefix}:{self.config.analysis_prefix}:*"
            keys = await self.redis.keys(pattern)
            
            if keys:
                deleted_count = await self.redis.delete(*keys)
                logger.info(f"Invalidated {deleted_count} analysis cache entries")
                return deleted_count
            
            return 0
            
        except Exception as e:
            logger.error(f"Error invalidating analysis cache: {e}")
            return 0
    
    async def clear_all_cache(self) -> int:
        """Clear all cache data."""
        if not self._connected:
            return 0
        
        try:
            pattern = f"{self.config.prefix}:*"
            keys = await self.redis.keys(pattern)
            
            if keys:
                deleted_count = await self.redis.delete(*keys)
                logger.info(f"Cleared {deleted_count} cache entries")
                return deleted_count
                
            return 0
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return 0
    
    # Utility methods
    
    async def get_cached_files(self) -> List[str]:
        """Get list of files that have cached data."""
        if not self._connected:
            return []
        
        try:
            pattern = f"{self.config.prefix}:{self.config.metadata_prefix}:*"
            keys = await self.redis.keys(pattern)
            
            # Extract file paths from keys
            prefix_len = len(f"{self.config.prefix}:{self.config.metadata_prefix}:")
            file_paths = [key.decode('utf-8')[prefix_len:] for key in keys]
            
            return file_paths
            
        except Exception as e:
            logger.error(f"Error getting cached files list: {e}")
            return []
    
    async def estimate_cache_size(self) -> Dict[str, int]:
        """Estimate cache size by category."""
        if not self._connected:
            return {}
        
        try:
            categories = {
                "nodes": f"{self.config.prefix}:{self.config.nodes_prefix}:*",
                "edges": f"{self.config.prefix}:{self.config.edges_prefix}:*", 
                "analysis": f"{self.config.prefix}:{self.config.analysis_prefix}:*",
                "metadata": f"{self.config.prefix}:{self.config.metadata_prefix}:*"
            }
            
            sizes = {}
            for category, pattern in categories.items():
                keys = await self.redis.keys(pattern)
                sizes[category] = len(keys)
            
            return sizes
            
        except Exception as e:
            logger.error(f"Error estimating cache size: {e}")
            return {}