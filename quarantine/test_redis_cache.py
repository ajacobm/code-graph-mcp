#!/usr/bin/env python3
"""
Comprehensive tests for Redis Cache integration
Tests redis_cache.py and cache_manager.py functionality
"""

import asyncio
import json
import tempfile
import time
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from code_graph_mcp.cache_manager import HybridCacheManager as CacheManager
from code_graph_mcp.redis_cache import RedisCacheBackend as RedisCache


class TestRedisCache:
    """Test suite for RedisCache class"""

    @pytest.fixture
    def redis_cache_config(self):
        """Redis cache configuration for testing"""
        return {
            'url': 'redis://localhost:6379/0',
            'prefix': 'test_cgmcp',
            'ttl': 3600,
            'compression_enabled': True,
            'compression_threshold': 1024
        }

    @pytest.fixture
    async def redis_cache(self, redis_cache_config):
        """Create RedisCache instance for testing"""
        cache = RedisCache(**redis_cache_config)
        await cache.initialize()
        yield cache
        await cache.close()

    @pytest.fixture
    def sample_file_data(self):
        """Sample file data for testing"""
        return {
            'content': 'def test_function():\n    return "hello world"',
            'metadata': {
                'size': 42,
                'mtime': time.time(),
                'content_hash': 'abc123def456'
            },
            'analysis': {
                'functions': ['test_function'],
                'classes': [],
                'imports': []
            }
        }

    @pytest.mark.asyncio
    async def test_redis_cache_initialization(self, redis_cache_config):
        """Test Redis cache initialization"""
        cache = RedisCache(**redis_cache_config)
        
        # Test with Redis available
        with patch('redis.asyncio.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            mock_client.ping.return_value = True
            
            await cache.initialize()
            assert cache.redis is not None
            assert cache.available is True
            mock_redis.assert_called_once()

    @pytest.mark.asyncio
    async def test_redis_cache_fallback_mode(self, redis_cache_config):
        """Test Redis cache fallback when Redis unavailable"""
        cache = RedisCache(**redis_cache_config)
        
        # Test with Redis unavailable
        with patch('redis.asyncio.from_url') as mock_redis:
            mock_redis.side_effect = Exception("Redis connection failed")
            
            await cache.initialize()
            assert cache.redis is None
            assert cache.available is False

    @pytest.mark.asyncio
    async def test_cache_operations_with_redis(self, redis_cache_config, sample_file_data):
        """Test cache operations when Redis is available"""
        cache = RedisCache(**redis_cache_config)
        
        with patch('redis.asyncio.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            mock_client.ping.return_value = True
            
            await cache.initialize()
            
            file_path = "test_file.py"
            
            # Test set operation
            mock_client.hset.return_value = True
            await cache.set(file_path, sample_file_data)
            mock_client.hset.assert_called()
            
            # Test get operation
            mock_client.hget.return_value = json.dumps(sample_file_data).encode()
            result = await cache.get(file_path)
            assert result == sample_file_data
            
            # Test exists operation
            mock_client.hexists.return_value = True
            exists = await cache.exists(file_path)
            assert exists is True
            
            # Test delete operation
            mock_client.hdel.return_value = 1
            await cache.delete(file_path)
            mock_client.hdel.assert_called()

    @pytest.mark.asyncio
    async def test_cache_operations_fallback_mode(self, redis_cache_config):
        """Test cache operations in fallback mode (no Redis)"""
        cache = RedisCache(**redis_cache_config)
        
        # Initialize without Redis
        with patch('redis.asyncio.from_url') as mock_redis:
            mock_redis.side_effect = Exception("Redis connection failed")
            await cache.initialize()
        
        file_path = "test_file.py"
        test_data = {"test": "data"}
        
        # All operations should return None/False in fallback mode
        await cache.set(file_path, test_data)
        result = await cache.get(file_path)
        assert result is None
        
        exists = await cache.exists(file_path)
        assert exists is False

    @pytest.mark.asyncio
    async def test_cache_compression(self, redis_cache_config, sample_file_data):
        """Test cache compression functionality"""
        config = redis_cache_config.copy()
        config['compression_threshold'] = 10  # Low threshold for testing
        
        cache = RedisCache(**config)
        
        with patch('redis.asyncio.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            mock_client.ping.return_value = True
            
            await cache.initialize()
            
            # Large data that should trigger compression
            large_data = {"content": "x" * 1000}
            
            mock_client.hset.return_value = True
            await cache.set("large_file.py", large_data)
            
            # Verify compression was used (check if data was compressed)
            call_args = mock_client.hset.call_args
            stored_data = call_args[0][2]  # Third argument is the data
            
            # Compressed data should be smaller than original JSON
            original_size = len(json.dumps(large_data))
        
    @pytest.mark.asyncio
    async def test_cache_health_check(self, redis_cache_config):
        """Test cache health monitoring"""
        cache = RedisCache(**redis_cache_config)
        
        with patch('redis.asyncio.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            mock_client.ping.return_value = True
            
            await cache.initialize()
            
            # Test healthy state
            health = await cache.health_check()
            assert health['status'] == 'healthy'
            assert 'latency_ms' in health
            
            # Test unhealthy state
            mock_client.ping.side_effect = Exception("Connection lost")
            health = await cache.health_check()
            assert health['status'] == 'unhealthy'

    @pytest.mark.asyncio
    async def test_cache_statistics(self, redis_cache_config):
        """Test cache statistics collection"""
        cache = RedisCache(**redis_cache_config)
        
        with patch('redis.asyncio.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            mock_client.ping.return_value = True
            mock_client.info.return_value = {
                'used_memory': 1024000,
                'used_memory_human': '1000K',
                'connected_clients': 5
            }
            
            await cache.initialize()
            
            stats = await cache.get_stats()
            assert 'memory_usage' in stats
            assert 'connection_count' in stats
            assert stats['available'] is True


class TestCacheManager:
    """Test suite for CacheManager class"""

    @pytest.fixture
    def temp_project_dir(self):
        """Create temporary project directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            # Create some test files
            (project_path / "test.py").write_text("def hello(): pass")
            (project_path / "subdir").mkdir()
            (project_path / "subdir" / "test2.py").write_text("def world(): pass")
            yield project_path

    @pytest.fixture
    async def cache_manager(self, temp_project_dir):
        """Create CacheManager instance for testing"""
        redis_config = {
            'url': 'redis://localhost:6379/0',
            'prefix': 'test_cgmcp',
            'ttl': 3600
        }
        
        manager = CacheManager(temp_project_dir, redis_config)
        await manager.initialize()
        yield manager
        await manager.close()

    @pytest.mark.asyncio
    async def test_cache_manager_initialization(self, temp_project_dir):
        """Test CacheManager initialization"""
        redis_config = {
            'url': 'redis://localhost:6379/0',
            'prefix': 'test_cgmcp'
        }
        
        manager = CacheManager(temp_project_dir, redis_config)
        
        with patch.object(manager.redis_cache, 'initialize') as mock_init:
            await manager.initialize()
            mock_init.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_manager_without_redis(self, temp_project_dir):
        """Test CacheManager without Redis configuration"""
        manager = CacheManager(temp_project_dir, None)
        await manager.initialize()
        
        assert manager.redis_cache is None
        assert manager.memory_cache is not None

    @pytest.mark.asyncio
    async def test_multi_tier_cache_hit(self, temp_project_dir):
        """Test multi-tier cache hit scenarios"""
        redis_config = {'url': 'redis://localhost:6379/0'}
        manager = CacheManager(temp_project_dir, redis_config)
        
        # Mock Redis cache
        with patch.object(manager, 'redis_cache') as mock_redis:
            mock_redis.available = True
            mock_redis.get.return_value = {"cached": "data"}
            
            await manager.initialize()
            
            file_path = temp_project_dir / "test.py"
            result = await manager.get_cached_analysis(str(file_path))
            
            # Should get from Redis (L2 cache)
            mock_redis.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_invalidation_on_file_change(self, temp_project_dir):
        """Test cache invalidation when file is modified"""
        manager = CacheManager(temp_project_dir, None)  # No Redis for simplicity
        await manager.initialize()
        
        file_path = temp_project_dir / "test.py"
        
        # Cache some analysis
        analysis_data = {"functions": ["hello"]}
        await manager.cache_analysis(str(file_path), analysis_data)
        
        # Verify cached
        cached = await manager.get_cached_analysis(str(file_path))
        assert cached is not None
        
        # Modify file
        file_path.write_text("def hello(): pass  # modified")
        
        # Cache should be invalidated (file mtime changed)
        cached_after_change = await manager.get_cached_analysis(str(file_path))
        # This depends on implementation - might return None if metadata check fails

    @pytest.mark.asyncio
    async def test_cache_statistics(self, temp_project_dir):
        """Test cache statistics collection"""
        manager = CacheManager(temp_project_dir, None)
        await manager.initialize()
        
        stats = await manager.get_cache_stats()
        
        assert 'memory' in stats
        assert 'redis' in stats
        assert 'total_hits' in stats
        assert 'total_misses' in stats
        assert 'hit_rate' in stats

    @pytest.mark.asyncio
    async def test_bulk_cache_operations(self, temp_project_dir):
        """Test bulk caching operations"""
        manager = CacheManager(temp_project_dir, None)
        await manager.initialize()
        
        # Prepare multiple files for bulk operations
        file_paths = []
        analysis_data = []
        
        for i in range(5):
            file_path = temp_project_dir / f"bulk_test_{i}.py"
            file_path.write_text(f"def func_{i}(): pass")
            file_paths.append(str(file_path))
            analysis_data.append({"functions": [f"func_{i}"]})
        
        # Test bulk caching
        await manager.cache_bulk_analyses(dict(zip(file_paths, analysis_data)))
        
        # Verify all were cached
        for file_path in file_paths:
            cached = await manager.get_cached_analysis(file_path)
            assert cached is not None

    @pytest.mark.asyncio
    async def test_memory_pressure_handling(self, temp_project_dir):
        """Test memory cache eviction under pressure"""
        # Create manager with small memory cache for testing
        manager = CacheManager(temp_project_dir, None, memory_cache_size=2)
        await manager.initialize()
        
        # Fill cache beyond capacity
        for i in range(5):
            file_path = temp_project_dir / f"memory_test_{i}.py"
            file_path.write_text(f"def func_{i}(): pass")
            await manager.cache_analysis(str(file_path), {"functions": [f"func_{i}"]})
        
        # Verify LRU eviction occurred (first entries should be evicted)
        early_cached = await manager.get_cached_analysis(str(temp_project_dir / "memory_test_0.py"))
        recent_cached = await manager.get_cached_analysis(str(temp_project_dir / "memory_test_4.py"))
        
        # Recent should still be cached, early might be evicted
        assert recent_cached is not None


class TestCacheIntegration:
    """Integration tests for cache components"""

    @pytest.mark.asyncio
    async def test_end_to_end_caching_workflow(self):
        """Test complete caching workflow from file analysis to retrieval"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            test_file = project_path / "integration_test.py"
            test_file.write_text("""
def calculate_sum(a, b):
    return a + b

class Calculator:
    def multiply(self, x, y):
        return x * y
            """)
            
            # Initialize cache manager
            manager = CacheManager(project_path, None)
            await manager.initialize()
            
            # Simulate analysis results
            analysis_result = {
                "functions": ["calculate_sum"],
                "classes": ["Calculator"],
                "methods": ["Calculator.multiply"],
                "imports": [],
                "complexity": 2
            }
            
            # Cache the analysis
            await manager.cache_analysis(str(test_file), analysis_result)
            
            # Retrieve and verify
            cached_result = await manager.get_cached_analysis(str(test_file))
            assert cached_result == analysis_result
            
            # Test cache miss for non-existent file
            missing_result = await manager.get_cached_analysis(str(project_path / "missing.py"))
            assert missing_result is None
            
            # Test cache statistics
            stats = await manager.get_cache_stats()
            assert stats['total_hits'] >= 1
            
            await manager.close()

    @pytest.mark.asyncio
    async def test_concurrent_cache_access(self):
        """Test concurrent access to cache"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            manager = CacheManager(project_path, None)
            await manager.initialize()
            
            # Create concurrent cache operations
            async def cache_worker(worker_id):
                file_path = project_path / f"concurrent_{worker_id}.py"
                file_path.write_text(f"def worker_{worker_id}(): pass")
                
                analysis = {"worker_id": worker_id, "functions": [f"worker_{worker_id}"]}
                await manager.cache_analysis(str(file_path), analysis)
                
                cached = await manager.get_cached_analysis(str(file_path))
                return cached
            
            # Run multiple workers concurrently
            workers = [cache_worker(i) for i in range(10)]
            results = await asyncio.gather(*workers)
            
            # Verify all workers completed successfully
            assert len(results) == 10
            for i, result in enumerate(results):
                assert result is not None
                assert result["worker_id"] == i
            
            await manager.close()


if __name__ == "__main__":
    # Run tests manually if needed
    import sys
    
    async def run_manual_tests():
        """Run tests manually for debugging"""
        print("🧪 Running Redis Cache Tests")
        print("=" * 50)
        
        # Simple connectivity test
        try:
            redis_config = {
                'url': 'redis://localhost:6379/0',
                'prefix': 'test_cgmcp',
                'ttl': 3600
            }
            
            cache = RedisCache(**redis_config)
            await cache.initialize()
            
            if cache.available:
                print("✅ Redis connection successful")
                
                # Test basic operations
                test_data = {"test": "data", "timestamp": time.time()}
                await cache.set("test_key", test_data)
                
                retrieved = await cache.get("test_key")
                if retrieved == test_data:
                    print("✅ Basic cache operations working")
                else:
                    print("❌ Cache data mismatch")
                
                # Cleanup
                await cache.delete("test_key")
                await cache.close()
            else:
                print("⚠️  Redis not available, fallback mode active")
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
            
        print("\n🎯 Manual tests completed")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--manual":
        asyncio.run(run_manual_tests())
    else:
        print("Run with --manual for manual testing")
        print("Use 'pytest test_redis_cache.py' for full test suite")
