#!/bin/bash
# Quick development server for Codespaces

set -e

# Default values
MODE=${1:-sse}
PORT=${2:-8000}
REDIS_URL=${REDIS_URL:-redis://localhost:6379}

echo "🚀 Starting codenav in Codespaces..."
echo ""
echo "Mode: $MODE"
echo "Port: $PORT"
echo "Redis: $REDIS_URL"
echo ""

# Check if Redis is running
if ! docker ps | grep -q codenav-redis; then
    echo "⚠️  Redis not running, starting..."
    ./scripts/codespaces-redis.sh
    echo ""
fi

# Start server
echo "Starting server..."
exec uv run codenav \
    --mode "$MODE" \
    --host 0.0.0.0 \
    --port "$PORT" \
    --enable-cache \
    --redis-url "$REDIS_URL" \
    --verbose
