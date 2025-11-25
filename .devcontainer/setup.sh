#!/bin/bash
# Codespace post-create setup script

set -e

echo "🚀 Setting up CodeNavigator (codenav) development environment..."
echo ""

# Install uv
echo "📦 Installing uv..."
pip install uv
echo ""

# Sync Python dependencies
echo "📦 Installing Python dependencies..."
uv sync --all-extras --dev
echo ""

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd frontend && npm ci && cd ..
echo ""

# Make scripts executable
echo "🔧 Making scripts executable..."
chmod +x scripts/*.sh
echo ""

# Create data directories
echo "📁 Creating data directories..."
mkdir -p /workspace/.redis-data
mkdir -p .pytest_cache
echo ""

# Install pre-commit hooks (optional)
if [ -f ".pre-commit-config.yaml" ]; then
    echo "🔧 Installing pre-commit hooks..."
    pip install pre-commit
    pre-commit install
fi
echo ""

echo "✅ Development environment setup complete!"
echo ""
echo "Quick start commands:"
echo "  ./scripts/codespaces-redis.sh    # Start Redis"
echo "  ./scripts/test-codespaces.sh     # Test setup"
echo "  ./scripts/dev-server.sh          # Start dev server"
echo ""
