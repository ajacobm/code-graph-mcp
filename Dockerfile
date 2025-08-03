# Multi-stage Dockerfile for Code Graph MCP Server
# Supports both stdio (MCP) and SSE (HTTP) modes with optional Redis caching
# Redis caching is automatically enabled when Redis is available via --enable-cache flag

FROM python:3.12-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies required for ast-grep, rustworkx, and Redis
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash --uid 1000 codeuser

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Install UV package manager
RUN pip install uv

# Development stage
FROM base AS development

# Install dependencies with dev extras
RUN uv sync --all-extras

# Copy source code
COPY . .

# Change ownership to non-root user
RUN chown -R codeuser:codeuser /app

USER codeuser

# Default command for development (stdio mode)
CMD ["uv", "run", "code-graph-mcp", "--verbose"]

# Production stage
FROM base AS production

# Copy source code and dependencies first
COPY src/ ./src/
COPY pyproject.toml ./
COPY README.md LICENSE ./

# Install only production dependencies and build
RUN uv sync --frozen --no-dev

# Install the package
RUN uv pip install -e .

# Change ownership to non-root user
RUN chown -R codeuser:codeuser /app

USER codeuser

# Create directories that might be needed
RUN mkdir -p /app/workspace /app/.cache

# Expose port for SSE mode
EXPOSE 8000

# Health check for the container
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Default command (can be overridden)
CMD ["code-graph-mcp", "--help"]

# SSE-specific stage
FROM production AS sse

# Default to SSE mode with HTTP server and Redis support (when available)
CMD ["code-graph-mcp", "--mode", "sse", "--host", "0.0.0.0", "--port", "8000", "--enable-cache"]

# Stdio-specific stage (for MCP clients)
FROM production AS stdio

# Default to stdio mode for MCP with Redis support (when available)
CMD ["code-graph-mcp", "--mode", "stdio", "--enable-cache"]