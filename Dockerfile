# Multi-stage Dockerfile for Code Graph MCP Server
# Supports both stdio (MCP) and SSE (HTTP) modes

FROM python:3.12-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies required for ast-grep and rustworkx
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
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
FROM base as development

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
FROM base as production

# Install only production dependencies
RUN uv sync --frozen --no-dev

# Copy source code
COPY . .

# Install the package
RUN uv pip install -e .

# Change ownership to non-root user
RUN chown -R codeuser:codeuser /app

USER codeuser

# Create directories that might be needed
RUN mkdir -p /app/workspace

# Expose port for SSE mode
EXPOSE 8000

# Default command (can be overridden)
CMD ["code-graph-mcp"]

# SSE-specific stage
FROM production as sse

# Default to SSE mode with HTTP server
CMD ["code-graph-mcp", "--mode", "sse", "--host", "0.0.0.0", "--port", "8000"]

# Stdio-specific stage (for MCP clients)
FROM production as stdio

# Default to stdio mode for MCP
CMD ["code-graph-mcp", "--mode", "stdio"]