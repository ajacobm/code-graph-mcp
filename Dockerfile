# Multi-stage Dockerfile for CodeNavigator (codenav)
# Supports stdio (MCP), HTTP (streamableHttp), and Web REST API modes
# Use --target flag to select: development | production | sse | http | stdio

FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash --uid 1000 codeuser

WORKDIR /app

COPY pyproject.toml uv.lock* ./

RUN pip install uv

# Development stage - full setup with dev dependencies
FROM base AS development

COPY . .

RUN uv sync --all-extras

RUN chown -R codeuser:codeuser /app

USER codeuser

RUN mkdir -p /app/workspace /app/.cache

EXPOSE 8000

CMD ["uv", "run", "codenav", "--mode", "sse", "--host", "0.0.0.0", "--port", "8000", "--enable-cache", "--verbose"]

# Production stage - minimal production dependencies
FROM base AS production

COPY src/ ./src/
COPY pyproject.toml ./
COPY README.md LICENSE ./

# Install with mcp and web extras for server functionality
RUN uv sync --frozen --no-dev --extra mcp --extra web

RUN uv pip install -e .

RUN chown -R codeuser:codeuser /app

USER codeuser

RUN mkdir -p /app/workspace /app/.cache

# Add virtual environment bin to PATH so codenav command is found
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["codenav", "--help"]

# SSE mode - MCP server with HTTP streaming (streamableHttp transport)
FROM production AS sse

CMD ["codenav", "--mode", "sse", "--host", "0.0.0.0", "--port", "8000", "--enable-cache"]

# HTTP mode - FastAPI REST server for frontend
FROM production AS http

CMD ["codenav-web", "--host", "0.0.0.0", "--port", "8000"]

# Stdio mode - MCP server with stdio transport
FROM production AS stdio

CMD ["codenav", "--mode", "stdio", "--enable-cache"]

# Test stage - includes test dependencies and test runner
FROM development AS test

# Copy test files
COPY tests/ ./tests/
COPY pytest.ini ./

# Install test dependencies
RUN uv sync --all-extras --dev

# Run tests by default
CMD ["uv", "run", "pytest", "-v", "--tb=short", "--color=yes"]
