# CodeNavigator Test Suite

This directory contains comprehensive tests for the CodeNavigator server, including tests for the new Redis cache integration and SSE server functionality.

## Test Structure

### Core Test Files

1. **`test_redis_cache.py`** - Redis cache functionality tests
   - `TestRedisCache` - Redis connection, operations, compression, health checks
   - `TestCacheManager` - Multi-tier cache management, invalidation, statistics
   - `TestCacheIntegration` - End-to-end caching workflows

2. **`test_sse_server.py`** - SSE (Server-Sent Events) server tests
   - `TestSSEServer` - FastAPI app creation, endpoint testing
   - `TestSSEServerWithCache` - SSE server with Redis integration
   - `TestSSEErrorHandling` - Error scenarios and graceful degradation

3. **`test_mcp_cache_integration.py`** - Integration tests
   - `TestMCPCacheIntegration` - MCP tools with caching
   - `TestMCPStdioIntegration` - MCP stdio interface with cache
   - End-to-end performance benchmarks

4. **`test_mcp_server.py`** - Enhanced MCP server tests
   - Original 8 MCP tools testing
   - Redis cache integration testing
   - Performance benchmarks
   - SSE server functionality testing

### Legacy Test Files

- `test_mcp_tools.py` - Original MCP tools testing
- `test_ast_grep.py` - AST and tree-sitter functionality
- `test_multi_language.py` - Multi-language support
- `test_rustworkx_graph.py` - Graph analysis with RustworkX
- `test_tool_schema.py` - Tool schema validation

## Quick Start

### Install Test Dependencies

```bash
# Install test requirements
pip install -r tests/test-requirements.txt

# Or if using uv
uv pip install -r tests/test-requirements.txt
```

### Run All Tests

```bash
# Run comprehensive test suite
python tests/run_tests.py

# Or use pytest directly
pytest tests/ -v
```

### Run Specific Test Suites

```bash
# Redis cache tests only
python tests/run_tests.py --redis-only

# SSE server tests only  
python tests/run_tests.py --sse-only

# Integration tests only
python tests/run_tests.py --integration-only

# Individual test files
pytest tests/test_redis_cache.py -v
pytest tests/test_sse_server.py -v
pytest tests/test_mcp_cache_integration.py -v
```

### Manual Testing

Some tests include manual testing modes for debugging:

```bash
# Manual Redis cache testing
python tests/test_redis_cache.py --manual

# Manual SSE server testing  
python tests/test_sse_server.py --manual

# Manual integration testing
python tests/test_mcp_cache_integration.py --manual
```

## Test Categories

### Unit Tests (`pytest -m unit`)

- Individual component testing
- Mock-heavy, fast execution
- No external dependencies required

### Integration Tests (`pytest -m integration`)

- Component interaction testing
- May require Redis, but will fallback gracefully
- End-to-end workflow testing

### Performance Tests (`pytest -m performance`)

- Cache performance benchmarks
- MCP tool execution timing
- Memory usage analysis

### Redis Tests (`pytest -m redis`)

- Requires Redis server
- Cache operations and clustering
- Will skip if Redis unavailable

## Test Configuration

### Redis Requirements

For Redis-dependent tests:

```bash
# Start Redis locally
redis-server

# Or use Docker
docker run -d -p 6379:6379 redis:7-alpine

# Tests will fallback to memory-only mode if Redis unavailable
```

### Environment Variables

```bash
# Optional: Custom Redis configuration
export REDIS_URL="redis://localhost:6379/0"
export REDIS_TEST_DB="15"  # Use different DB for tests

# Enable debug output
export CODE_GRAPH_DEBUG="1"
```

## Test Output

### Pytest Output

```bash
# Verbose output with timing
pytest tests/ -v --durations=10

# With coverage
pytest tests/ --cov=codenav --cov-report=html

# Only fast tests
pytest tests/ -m "not slow"
```

### Manual Test Output

Manual tests provide detailed output for debugging:

```
🧪 Running Redis Cache Tests
==================================================
✅ Redis connection successful
✅ Basic cache operations working  
📊 Cache stats: {'hits': 2, 'misses': 1, 'hit_rate': 0.67}
🎯 Manual tests completed
```

## Troubleshooting

### Common Issues

1. **Redis Connection Failed**
   ```
   ⚠️ Redis not available, fallback mode active
   ```
   - Tests will continue with memory-only caching
   - Install and start Redis for full functionality

2. **Import Errors**
   ```
   ImportError: No module named 'codenav'
   ```
   - Install the package in development mode: `pip install -e .`
   - Ensure you're in the project root directory

3. **MCP Tools Not Found**
   ```
   FileNotFoundError: codenav command not found
   ```
   - Install the package: `pip install -e .`
   - Or run tests from project root with `python -m`

4. **Timeout Errors**
   ```
   TimeoutError: Test exceeded 300s
   ```
   - Large projects may take longer to analyze
   - Increase timeout in `pytest.ini` if needed
   - Use `--timeout=600` flag

### Performance Expectations

- **Unit tests**: < 1 second each
- **Integration tests**: 5-30 seconds each  
- **Performance tests**: 30-120 seconds each
- **Full suite**: 3-10 minutes (depends on Redis availability)

### Cache Performance Indicators

Good cache performance should show:
- **95%+ hit rate** after warmup period
- **2-10x speedup** on repeated operations
- **Sub-second response times** for cached data

## Extending Tests

### Adding New Test Cases

1. **Create test file**: Follow naming convention `test_*.py`
2. **Use fixtures**: Leverage existing fixtures for common setup
3. **Mark appropriately**: Use pytest markers (@pytest.mark.redis, etc.)
4. **Include cleanup**: Ensure tests clean up resources
5. **Update runner**: Add to `run_tests.py` if needed

### Test Fixtures

Common fixtures available:

```python
@pytest.fixture
def temp_project_dir():
    """Temporary project with test files"""

@pytest.fixture  
async def redis_cache(redis_cache_config):
    """Redis cache instance"""

@pytest.fixture
async def cache_manager(temp_project_dir):
    """Cache manager with memory + Redis"""

@pytest.fixture
def test_app(temp_project_dir):
    """FastAPI test application"""
```

### Mock Patterns

```python
# Mock Redis when testing fallback
with patch('redis.asyncio.from_url') as mock_redis:
    mock_redis.side_effect = Exception("Redis unavailable")
    # Test fallback behavior

# Mock file system for edge cases  
with patch('pathlib.Path.exists') as mock_exists:
    mock_exists.return_value = False
    # Test missing file scenarios
```

## Continuous Integration

For CI/CD pipelines:

```yaml
# GitHub Actions example
- name: Install dependencies
  run: pip install -r tests/test-requirements.txt

- name: Start Redis
  run: redis-server --daemonize yes

- name: Run tests
  run: python tests/run_tests.py

- name: Upload coverage
  run: pytest tests/ --cov=codenav --cov-report=xml
```

Tests are designed to be resilient and will skip Redis-dependent functionality when Redis is unavailable, making them suitable for environments where Redis cannot be installed.

## Performance Benchmarks

Expected performance with Redis caching enabled:

| Operation | Cold Cache | Warm Cache | Speedup |
|-----------|------------|------------|---------|
| Analyze Codebase | 2-10s | 0.1-0.5s | 5-20x |
| Find Definition | 0.5-2s | 0.01-0.1s | 10-50x |
| Find References | 1-5s | 0.05-0.2s | 10-25x |
| Complexity Analysis | 1-3s | 0.1-0.3s | 5-15x |

Results vary based on project size, file count, and Redis configuration.
