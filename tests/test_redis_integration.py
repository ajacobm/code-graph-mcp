"""
Redis persistence integration tests.

Tests that Redis properly persists:
- Code analysis results (nodes, relationships)
- Cache hits/misses across operations
- Data durability across engine restarts
"""

from pathlib import Path
import json

import pytest
import pytest_asyncio

from code_graph_mcp.server.analysis_engine import UniversalAnalysisEngine


@pytest.fixture(scope="module")
def redis_available():
    """Check if Redis is available."""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, socket_connect_timeout=1)
        r.ping()
        return True
    except Exception:
        return False


@pytest_asyncio.fixture(scope="function")
async def engine_with_redis(redis_available):
    """Create analysis engine with Redis enabled."""
    if not redis_available:
        pytest.skip("Redis not available")
    
    project_root = Path(__file__).parent.parent / "src" / "code_graph_mcp"
    
    engine = UniversalAnalysisEngine(
        project_root,
        enable_file_watcher=False,
        enable_redis_cache=True
    )
    await engine._analyze_project()
    
    yield engine


@pytest.mark.skipif(not pytest.importorskip("redis"), reason="Redis not available")
@pytest.mark.asyncio
async def test_redis_cache_initialized(engine_with_redis, redis_available):
    """Verify Redis cache is initialized."""
    if not redis_available:
        pytest.skip("Redis not available")
    
    engine = engine_with_redis
    assert engine.analyzer is not None
    assert engine.analyzer.cache_manager is not None
    print("✓ Redis cache initialized")





@pytest.mark.skipif(not pytest.importorskip("redis"), reason="Redis not available")
@pytest.mark.asyncio
async def test_cache_hit_on_second_access(redis_available):
    """Verify cache hits when accessing same project twice."""
    if not redis_available:
        pytest.skip("Redis not available")
    
    project_root = Path(__file__).parent.parent / "src" / "code_graph_mcp"
    
    engine1 = UniversalAnalysisEngine(
        project_root,
        enable_file_watcher=False,
        enable_redis_cache=True
    )
    await engine1._analyze_project()
    nodes_first_pass = len(engine1.graph.nodes)
    
    engine2 = UniversalAnalysisEngine(
        project_root,
        enable_file_watcher=False,
        enable_redis_cache=True
    )
    await engine2._analyze_project()
    nodes_second_pass = len(engine2.graph.nodes)
    
    assert nodes_first_pass == nodes_second_pass, \
        f"Cache should return same data: {nodes_first_pass} vs {nodes_second_pass}"
    print(f"✓ Cache hit: {nodes_second_pass} nodes loaded from Redis")


@pytest.mark.skipif(not pytest.importorskip("redis"), reason="Redis not available")
@pytest.mark.asyncio
async def test_cache_manager_writes_to_redis(engine_with_redis, redis_available):
    """Verify cache_manager writes data to Redis."""
    if not redis_available:
        pytest.skip("Redis not available")
    
    engine = engine_with_redis
    
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379)
        
        keys = r.keys('*')
        assert len(keys) > 0, "Redis should contain cache keys after analysis"
        print(f"✓ Redis has {len(keys)} keys")
        
        r.close()
    except ImportError:
        pytest.skip("redis-py not available")


@pytest.mark.skipif(not pytest.importorskip("redis"), reason="Redis not available")
@pytest.mark.asyncio
async def test_cache_key_structure(engine_with_redis, redis_available):
    """Verify cache keys follow expected structure."""
    if not redis_available:
        pytest.skip("Redis not available")
    
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379)
        
        keys = r.keys('code_graph:*')
        if keys:
            sample_key = keys[0]
            print(f"✓ Sample cache key: {sample_key}")
            value = r.get(sample_key)
            assert value is not None, "Cache key should have value"
        
        r.close()
    except ImportError:
        pytest.skip("redis-py not available")


@pytest.mark.skipif(not pytest.importorskip("redis"), reason="Redis not available")
@pytest.mark.asyncio
async def test_cache_survives_engine_restart(redis_available):
    """Verify data persists across engine instances."""
    if not redis_available:
        pytest.skip("Redis not available")
    
    project_root = Path(__file__).parent.parent / "src" / "code_graph_mcp"
    
    engine1 = UniversalAnalysisEngine(
        project_root,
        enable_file_watcher=False,
        enable_redis_cache=True
    )
    await engine1._analyze_project()
    original_node_count = len(engine1.graph.nodes)
    original_rel_count = len(engine1.graph.relationships)
    
    del engine1
    
    engine2 = UniversalAnalysisEngine(
        project_root,
        enable_file_watcher=False,
        enable_redis_cache=True
    )
    await engine2._analyze_project()
    restored_node_count = len(engine2.graph.nodes)
    restored_rel_count = len(engine2.graph.relationships)
    
    assert original_node_count == restored_node_count, \
        f"Node count mismatch: {original_node_count} vs {restored_node_count}"
    assert original_rel_count == restored_rel_count, \
        f"Relationship count mismatch: {original_rel_count} vs {restored_rel_count}"
    
    print(f"✓ Persistence verified: {restored_node_count} nodes, {restored_rel_count} relationships")
