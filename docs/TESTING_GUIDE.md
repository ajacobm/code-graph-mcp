# Testing Infrastructure Guide

## Overview

We have **4 testing layers** for code-graph-mcp:

1. **Unit Tests** - Fast, isolated, no external dependencies
2. **Integration Tests** - With Redis, full MCP protocol
3. **Docker Tests** - Containerized test environment
4. **Frontend Tests** - Build validation, linting (future: E2E)

## Test Infrastructure

### Test Docker Image

**Dockerfile target**: `test`

```dockerfile
FROM development AS test
COPY tests/ ./tests/
COPY pytest.ini ./
RUN uv sync --all-extras --dev
CMD ["uv", "run", "pytest", "-v", "--tb=short", "--color=yes"]
```

**Features**:
- Based on development image (all dependencies)
- Includes test files and configuration
- Can run standalone or in CI/CD
- Cached for fast rebuilds

**Build and run**:
```bash
# Build test image
docker build --target test -t codegraph-test .

# Run all tests
docker run --rm codegraph-test

# Run with Redis
docker run -d --name redis -p 6379:6379 redis:alpine
docker run --rm --network host -e REDIS_URL=redis://localhost:6379 codegraph-test
```

**GHCR image**: `ghcr.io/ajacobm/code-graph-mcp:test-latest`

### GitHub Actions Test Workflow

**File**: `.github/workflows/test.yml`

**Jobs**:

1. **unit-tests** (Matrix: Python 3.11, 3.12)
   - Fast unit tests without external dependencies
   - Runs on every push and PR
   - ~2-5 minutes

2. **integration-tests**
   - Full tests with Redis service
   - Tests MCP protocol, caching, SSE
   - ~5-10 minutes

3. **docker-test**
   - Builds test Docker image
   - Runs tests in containerized environment
   - Pushes test image to GHCR (main branch only)
   - ~5-8 minutes

4. **frontend-tests**
   - Lints and builds frontend
   - Validates Vue.js compilation
   - ~2-3 minutes

5. **coverage**
   - Runs all tests with coverage tracking
   - Uploads to Codecov
   - Generates HTML coverage report
   - ~5-10 minutes

**Total**: ~15-30 minutes for complete test suite

## Test Organization

### Test Markers

Defined in `pytest.ini`:

```python
# Run only unit tests (fast)
pytest -m "unit"

# Run only integration tests
pytest -m "integration"

# Skip slow tests
pytest -m "not slow"

# Run Redis-dependent tests
pytest -m "redis"

# Run SSE server tests
pytest -m "sse"

# Run MCP protocol tests
pytest -m "mcp"
```

### Test Structure

```
tests/
├── test_ast_grep.py              # AST parsing tests
├── test_backend_graph_queries.py # Graph query tests
├── test_calls_implementation.py  # Function call detection
├── test_entry_detector.py        # Entry point detection
├── test_graph_queries.py         # Graph operations
├── test_mcp_server.py            # MCP protocol tests
├── test_mcp_tools.py             # MCP tool tests
├── test_redis_integration.py     # Redis caching tests
├── test_sse_server.py            # SSE server tests
└── conftest.py                   # Pytest fixtures
```

## Running Tests

### Local Development

**Quick unit tests** (no external deps):
```bash
pytest -v -m "not integration and not redis"
```

**With Redis**:
```bash
# Terminal 1: Start Redis
./scripts/codespaces-redis.sh

# Terminal 2: Run tests
REDIS_URL=redis://localhost:6379 pytest -v
```

**Specific test file**:
```bash
pytest tests/test_mcp_tools.py -v
```

**Specific test function**:
```bash
pytest tests/test_mcp_tools.py::test_analyze_codebase -v
```

**With coverage**:
```bash
pytest --cov=src/code_graph_mcp --cov-report=html
open htmlcov/index.html
```

### Docker Testing

**Using test image**:
```bash
# Build
docker build --target test -t codegraph-test .

# Run
docker run --rm codegraph-test

# Run specific tests
docker run --rm codegraph-test pytest tests/test_mcp_tools.py -v
```

**Using docker-compose**:
```bash
# Run tests with Redis
docker compose -f docker-compose-test.yml up --abort-on-container-exit

# Or create a simple test compose file
cat > docker-compose-test.yml << 'EOF'
services:
  redis:
    image: redis:alpine
    
  test:
    build:
      context: .
      target: test
    depends_on:
      - redis
    environment:
      - REDIS_URL=redis://redis:6379
EOF

docker compose -f docker-compose-test.yml up --abort-on-container-exit
```

### Codespaces Testing

**Full test suite**:
```bash
# Start Redis
./scripts/codespaces-redis.sh

# Run all tests
uv run pytest -v

# Run with coverage
uv run pytest --cov=src/code_graph_mcp --cov-report=term --cov-report=html
```

**Watch mode** (auto-rerun on file changes):
```bash
uv run pytest-watch
```

## CI/CD Integration

### Automatic Testing

**Triggers**:
- ✅ Every push to `main` or `develop`
- ✅ Every pull request to `main`
- ✅ Manual dispatch

**What runs**:
1. Unit tests (Python 3.11, 3.12)
2. Integration tests (with Redis)
3. Docker test image build and test
4. Frontend build validation
5. Coverage report generation

**Results**:
- Test results uploaded as artifacts
- Coverage report on Codecov
- Test image pushed to GHCR (main branch)

### Viewing Test Results

**In GitHub Actions**:
```bash
# View latest run
gh run view

# Watch live
gh run watch

# Download artifacts
gh run download <run-id>
```

**Coverage badge** (add to README.md):
```markdown
[![codecov](https://codecov.io/gh/ajacobm/code-graph-mcp/branch/main/graph/badge.svg)](https://codecov.io/gh/ajacobm/code-graph-mcp)
```

## Test Image vs Other Images

| Image | Purpose | Size | Includes Tests | Use Case |
|-------|---------|------|----------------|----------|
| `test` | Running tests | ~800 MB | ✅ Yes | CI/CD, local testing |
| `development` | Development | ~800 MB | ❌ No | Active coding, debugging |
| `production` | Production | ~500 MB | ❌ No | Deployment, production use |
| `sse` | SSE server | ~500 MB | ❌ No | MCP SSE transport |
| `http` | HTTP API | ~500 MB | ❌ No | REST API server |
| `stdio` | stdio server | ~500 MB | ❌ No | CLI MCP transport |

**When to use test image**:
- ✅ Running full test suite in CI/CD
- ✅ Validating changes before deployment
- ✅ Debugging test failures in containerized env
- ✅ Ensuring tests pass in production-like environment

**When NOT to use test image**:
- ❌ Production deployment (use production/sse/http/stdio)
- ❌ Local development (use development or run directly)
- ❌ As a base for other images

## Frontend Testing

### Current Setup

```bash
cd frontend

# Install dependencies
npm ci

# Lint (if configured)
npm run lint

# Build validation
npm run build
```

### Future: E2E Tests

**Recommended**: Playwright or Cypress

```bash
# Install Playwright
npm install -D @playwright/test

# Run E2E tests
npm run test:e2e
```

**Example E2E test**:
```typescript
// tests/e2e/graph-visualization.spec.ts
import { test, expect } from '@playwright/test';

test('loads graph visualization', async ({ page }) => {
  await page.goto('http://localhost:5173');
  await expect(page.locator('#graph-canvas')).toBeVisible();
  
  // Click on a node
  await page.locator('.graph-node').first().click();
  await expect(page.locator('.node-details')).toBeVisible();
});
```

## Test Coverage Goals

**Current coverage**: Check Codecov badge

**Target coverage**:
- Overall: >80%
- Core modules: >90%
- MCP tools: >95%

**Coverage by module**:
```bash
pytest --cov=src/code_graph_mcp --cov-report=term-missing
```

## Continuous Testing Workflow

### Development Cycle

```bash
# 1. Write test first (TDD)
vim tests/test_new_feature.py

# 2. Run test (should fail)
pytest tests/test_new_feature.py -v

# 3. Implement feature
vim src/code_graph_mcp/new_feature.py

# 4. Run test again (should pass)
pytest tests/test_new_feature.py -v

# 5. Run full test suite
pytest -v

# 6. Check coverage
pytest --cov=src/code_graph_mcp --cov-report=term
```

### Pre-commit Testing

Create `.git/hooks/pre-commit`:
```bash
#!/bin/bash
set -e

echo "Running tests before commit..."
pytest -v -m "not slow and not integration"

echo "✅ Tests passed! Committing..."
```

```bash
chmod +x .git/hooks/pre-commit
```

## Troubleshooting Tests

### Tests Failing in CI but Passing Locally

**Common causes**:
1. Different Python version
2. Missing environment variables
3. Race conditions (timing issues)
4. External dependencies

**Solutions**:
```bash
# Test with same Python version as CI
pyenv install 3.12
pyenv local 3.12
pytest -v

# Run in Docker (matches CI environment)
docker build --target test -t test .
docker run --rm test

# Check environment variables
env | grep -E 'REDIS|CODEGRAPH'
```

### Redis Connection Errors

```bash
# Check Redis is running
redis-cli ping

# Start Redis if needed
./scripts/codespaces-redis.sh

# Check connection
python -c "import redis; r = redis.from_url('redis://localhost:6379'); print(r.ping())"
```

### Test Timeouts

```bash
# Increase timeout
pytest --timeout=300 -v

# Run with more verbose output
pytest -vv --tb=long
```

### Memory Issues

```bash
# Run tests sequentially (no parallelization)
pytest -v --maxfail=1

# Limit workers
pytest -v -n 2
```

## Performance Testing

### Load Testing

```bash
# Install locust
pip install locust

# Create load test
cat > locustfile.py << 'EOF'
from locust import HttpUser, task, between

class MCPUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def analyze_codebase(self):
        self.client.post("/analyze", json={"path": "/workspace"})
        
    @task
    def query_graph(self):
        self.client.get("/graph/nodes")
EOF

# Run load test
locust -f locustfile.py --host=http://localhost:8000
```

### Benchmark Tests

```python
# tests/test_performance.py
import pytest
import time

@pytest.mark.benchmark
def test_graph_build_performance(benchmark):
    def build_graph():
        # Your graph building code
        pass
    
    result = benchmark(build_graph)
    assert result < 5.0  # Should complete in < 5 seconds
```

## Next Steps

1. **Add coverage badge** to README
2. **Set up Codecov** integration
3. **Add E2E tests** for frontend
4. **Create performance benchmarks**
5. **Set up mutation testing** (optional)

## Documentation Links

- **Main README**: [README.md](../README.md)
- **Frontend Deployment**: [FRONTEND_DEPLOYMENT.md](FRONTEND_DEPLOYMENT.md)
- **Codespaces Guide**: [CODESPACES_INFRASTRUCTURE.md](CODESPACES_INFRASTRUCTURE.md)
- **GitHub Actions Docs**: https://docs.github.com/en/actions
- **Pytest Docs**: https://docs.pytest.org/
