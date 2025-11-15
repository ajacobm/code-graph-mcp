#!/bin/bash
# Start Redis for Codespaces development

set -e

echo "🚀 Starting Redis for Codespaces..."

# Check if Redis is already running
if docker ps | grep -q codegraph-redis; then
    echo "✅ Redis is already running"
    docker ps | grep codegraph-redis
    exit 0
fi

# Create data directory
mkdir -p /workspace/.redis-data

# Start Redis
docker run -d \
    --name codegraph-redis \
    -p 6379:6379 \
    -v /workspace/.redis-data:/data \
    redis:alpine \
    redis-server --appendonly yes

echo "⏳ Waiting for Redis to be ready..."
sleep 2

# Test connection
if docker exec codegraph-redis redis-cli ping | grep -q PONG; then
    echo "✅ Redis is ready!"
    echo ""
    echo "Redis URL: redis://localhost:6379"
    echo ""
    echo "Test connection:"
    echo "  redis-cli ping"
    echo ""
    echo "Stop Redis:"
    echo "  docker stop codegraph-redis && docker rm codegraph-redis"
else
    echo "❌ Redis failed to start"
    exit 1
fi
