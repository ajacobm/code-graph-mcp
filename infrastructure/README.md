# Infrastructure & Docker Compose Configuration

This directory contains Docker Compose configurations for CodeNav development.

## Quick Start

```bash
# Full development stack (everything)
make dev-up

# Backend only (for local frontend dev with npm)
make backend-up

# GitHub Codespaces
make codespaces-up

# Test GHCR production images
make ghcr-up
```

## Docker Compose Structure

### Base Configuration (`docker-compose.yml`)

The root compose file runs **all facilities**:

| Service | Port | Description |
|---------|------|-------------|
| `redis` | 6379 | Cache and session storage |
| `codenav-mcp` | 8000 | SSE/MCP server for AI agents |
| `codenav-web` | 10101 | HTTP REST API for frontend |
| `frontend` | 5173 | Vue.js development server |
| `memgraph` | 7687, 3000 | Graph database + Lab UI |
| `jupyter` | 8888 | Data science notebooks |
| `redis-insight` | 5540 | Redis monitoring (optional) |

```bash
# Start full stack
docker-compose -f infrastructure/docker-compose.yml up -d

# With Redis monitoring
docker-compose -f infrastructure/docker-compose.yml --profile monitoring up -d
```

### Profiles (Overlay Configurations)

Located in `profiles/` directory. Each modifies the base for specific use cases:

| Profile | Purpose | Use Case |
|---------|---------|----------|
| `backend-only.yml` | Redis + backend services only | Local frontend dev with `npm run dev` |
| `codespaces.yml` | GitHub Codespaces optimized | Dev in Codespaces with Playwright testing |
| `ghcr.yml` | Pre-built GHCR images | Test production builds without building |

```bash
# Example: Backend only
docker-compose -f infrastructure/docker-compose.yml \
               -f infrastructure/profiles/backend-only.yml up -d
```

## Profile Details

### Backend-Only (`profiles/backend-only.yml`)

For developing the frontend locally while backend runs in Docker:

- Uses GHCR images (no build required, fast startup)
- Enables CORS for `localhost:5173` and `localhost:5174`
- Disables: frontend, memgraph, jupyter

```bash
make backend-up
cd frontend && npm run dev  # Run frontend locally
```

### Codespaces (`profiles/codespaces.yml`)

Optimized for GitHub Codespaces development:

- Builds from source (development target)
- Includes frontend for Playwright testing
- Uses `/workspace` mount paths
- Disables heavy services (memgraph, jupyter) to save resources

```bash
make codespaces-up
```

### GHCR (`profiles/ghcr.yml`)

Tests pre-built production images from GitHub Container Registry:

- No building required
- Uses `ghcr.io/ajacobm/codenav:*` images
- Includes frontend (also from GHCR)
- Disables: memgraph, jupyter

```bash
docker login ghcr.io  # Authenticate first
make ghcr-up
```

## Environment Variables

Configure via environment or `.env` file:

```bash
# Workspace path (mounted into containers)
CODENAV_WORKSPACE=/path/to/your/repo

# Log level
CODENAV_LOG_LEVEL=DEBUG

# CORS origins for local development
CORS_ORIGINS=http://localhost:5173,http://localhost:5174
```

## Makefile Targets

```bash
make help              # Show all targets

# Full development
make dev-up            # Start full stack
make dev-down          # Stop
make dev-logs          # Follow logs
make dev-status        # Show container status
make dev-monitoring    # With Redis Insight

# Backend only
make backend-up        # Start backend only
make backend-down      # Stop

# Codespaces
make codespaces-up     # Start Codespaces stack
make codespaces-down   # Stop

# GHCR
make ghcr-up           # Start with GHCR images
make ghcr-down         # Stop
make ghcr-pull         # Pull latest images

# Infrastructure
make clean             # Remove all containers and volumes
make rebuild           # Rebuild all images
make ps                # Show running containers
```

## Common Tasks

### View logs for a specific service

```bash
docker-compose -f infrastructure/docker-compose.yml logs -f codenav-web
```

### Access service shell

```bash
docker-compose -f infrastructure/docker-compose.yml exec codenav-web bash
```

### Rebuild a specific service

```bash
docker-compose -f infrastructure/docker-compose.yml build --no-cache codenav-mcp
```

## Troubleshooting

### Port conflicts

Check if ports are already in use:

```bash
lsof -i :8000   # SSE server
lsof -i :10101  # HTTP API
lsof -i :5173   # Frontend
```

### Services fail health checks

```bash
# Check all logs
make dev-logs

# Check specific service
docker-compose -f infrastructure/docker-compose.yml logs codenav-mcp
```

### Clean restart

```bash
make clean      # Remove everything
make rebuild    # Rebuild images
make dev-up     # Start fresh
```

---

**Last Updated**: November 2025

