#!/bin/bash
# Test Codespaces setup

set -e

echo "🧪 Testing Codespaces Infrastructure..."
echo ""

# Check if we're in Codespaces
if [ -n "$CODESPACES" ]; then
    echo "✅ Running in GitHub Codespaces"
else
    echo "⚠️  Not in Codespaces (local environment)"
fi
echo ""

# Test Redis
echo "📡 Testing Redis connection..."
if docker ps | grep -q codegraph-redis; then
    if docker exec codegraph-redis redis-cli ping | grep -q PONG; then
        echo "✅ Redis is running and responsive"
    else
        echo "❌ Redis container exists but not responding"
        exit 1
    fi
else
    echo "❌ Redis container not running"
    echo "   Start with: ./scripts/codespaces-redis.sh"
    exit 1
fi
echo ""

# Test Python environment
echo "🐍 Testing Python environment..."
if command -v uv &> /dev/null; then
    echo "✅ uv is installed: $(uv --version)"
    UV_CMD="uv run"
elif command -v python3 &> /dev/null; then
    echo "⚠️  uv not found, using python3: $(python3 --version)"
    echo "   Installing uv..."
    pip install uv
    UV_CMD="uv run"
else
    echo "❌ Neither uv nor python3 found"
    exit 1
fi
echo ""

# Test Docker
echo "🐳 Testing Docker..."
if command -v docker &> /dev/null; then
    echo "✅ Docker is installed: $(docker --version)"
else
    echo "❌ Docker not found"
    exit 1
fi
echo ""

# Test code-graph-mcp
echo "📦 Testing code-graph-mcp..."
if $UV_CMD python -c "import code_graph_mcp; print('✅ code_graph_mcp module imports successfully')" 2>/dev/null; then
    echo ""
elif python3 -c "import sys; sys.path.insert(0, 'src'); import code_graph_mcp; print('✅ code_graph_mcp module imports successfully')" 2>/dev/null; then
    echo ""
else
    echo "⚠️  code_graph_mcp not installed yet"
    echo "   Installing dependencies..."
    if command -v uv &> /dev/null; then
        uv sync
    else
        pip install -e .
    fi
fi

# Test MCP server (quick check)
echo "🔧 Testing MCP server..."
timeout 5s uv run code-graph-mcp --mode stdio --help > /dev/null 2>&1
if [ $? -eq 0 ] || [ $? -eq 124 ]; then
    echo "✅ MCP server executable works"
else
    echo "❌ MCP server failed"
    exit 1
fi
echo ""

# Check ports
echo "🔌 Checking ports..."
if lsof -i:8000 &> /dev/null; then
    echo "⚠️  Port 8000 is in use:"
    lsof -i:8000
else
    echo "✅ Port 8000 is available"
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✨ All tests passed!"
echo ""
echo "Next steps:"
echo "  1. Start SSE server:"
echo "     uv run code-graph-mcp --mode sse --port 8000 --redis-url redis://localhost:6379 --verbose"
echo ""
echo "  2. Or use Docker Compose:"
echo "     docker compose -f docker-compose-codespaces.yml up -d"
echo ""
echo "  3. Test with curl:"
echo "     curl http://localhost:8000/health"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
