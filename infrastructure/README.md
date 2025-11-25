# Infrastructure & Docker Compose Configuration

This directory contains all Docker Compose configurations and related infrastructure files.

## Quick Start

```bash
# Development (default, includes everything)
make dev-up

# Testing
make test-up

# Backend only (frontend dev)
make backend-up

# GitHub Codespaces
make codespaces-up

# Production with GHCR
make ghcr-up
```

## Compose Files Organization

### Base Configuration

**`docker-compose.yml`** - Production-ready base configuration
- Redis, Memgraph, Backend API, Jupyter
- Standard networking and volume setup
- Health checks on all services
- **Use this**: As the foundation for all deployments

### Profiles (Variants)

Located in `profiles/` directory. Each adds specific services or configuration overrides:

| Profile | Purpose | Command |
|---------|---------|---------|
| **test.yml** | pytest/testing environment | `docker-compose -f docker-compose.yml -f profiles/test.yml up` |
| **codespaces.yml** | GitHub Codespaces optimizations | `docker-compose -f docker-compose.yml -f profiles/codespaces.yml up` |
| **backend-only.yml** | Backend services only (for local frontend dev) | `docker-compose -f docker-compose.yml -f profiles/backend-only.yml up` |
| **ghcr.yml** | GHCR image registry integration | `docker-compose -f docker-compose.yml -f profiles/ghcr.yml up` |
| **multi.yml** | Extended multi-service setup | `docker-compose -f docker-compose.yml -f profiles/multi.yml up` |
| **validation.yml** | CI/CD validation environment | `docker-compose -f docker-compose.yml -f profiles/validation.yml up` |
| **sample.yml** | Example/reference configuration | `docker-compose -f docker-compose.yml -f profiles/sample.yml up` |

## Using Compose Profiles

### Option 1: Make Commands (Recommended)

Use the Makefile from the root directory:

```bash
make dev-up          # Start development stack
make dev-down        # Stop development stack
make dev-logs        # View logs
make test-up         # Start testing environment
make backend-up      # Backend only
make codespaces-up   # Codespaces variant
make clean           # Remove all containers/volumes
```

### Option 2: Direct Docker Compose Commands

```bash
# Development (base only)
docker-compose -f docker-compose.yml up -d

# With test profile
docker-compose -f docker-compose.yml -f profiles/test.yml up -d

# With backend-only profile
docker-compose -f docker-compose.yml -f profiles/backend-only.yml up -d

# View logs
docker-compose -f docker-compose.yml logs -f code-graph-http

# Bring down
docker-compose -f docker-compose.yml down
```

### Option 3: Shell Aliases

Add to your `.bashrc` or `.zshrc`:

```bash
alias dc='docker-compose -f infrastructure/docker-compose.yml'
alias dctest='docker-compose -f infrastructure/docker-compose.yml -f infrastructure/profiles/test.yml'
alias dcback='docker-compose -f infrastructure/docker-compose.yml -f infrastructure/profiles/backend-only.yml'
alias dcspaces='docker-compose -f infrastructure/docker-compose.yml -f infrastructure/profiles/codespaces.yml'
```

Then:
```bash
dc up -d
dctest up -d
dcback up -d
```

## Environment Configuration

### Default Behavior (Codespaces)

By default, all services use Docker volumes (not bind mounts):

- `redis-data` - Redis persistence
- `memgraph-data` - Memgraph persistence
- `repo-mount` - Project repository mount

This is optimal for Codespaces and CI/CD environments.

### Local Development Overrides

For local development with persistent storage, create `docker-compose.override.yml`:

```bash
# Copy the example
cp docker-compose.override.yml.example docker-compose.override.yml

# Edit and add your bind mounts
nano docker-compose.override.yml
```

Example for local Linux development:

```yaml
services:
  redis:
    volumes:
      - ~/redis-data:/data

  code-graph-sse:
    volumes:
      - ~/code/codenav:/app
      - ~/code/codenav:/app/workspace

  memgraph:
    volumes:
      - ~/memgraph-data:/var/lib/memgraph
```

Example for Windows (WSL2):

```yaml
services:
  redis:
    volumes:
      - /mnt/c/Users/ADAM/.redis-docker/codegraphmcp:/data

  code-graph-sse:
    volumes:
      - /mnt/c/Users/ADAM/GitHub/codenav:/app
      - /mnt/c/Users/ADAM/GitHub/codenav:/app/workspace

  memgraph:
    volumes:
      - /mnt/c/Users/ADAM/.memgraph-docker/codegraphmcp:/var/lib/memgraph
```

**Note**: Docker Compose automatically loads `docker-compose.override.yml` if it exists in the same directory as `docker-compose.yml`. This allows you to customize settings without modifying the base configuration.

### Service Configuration Variables

Configure services via environment variables in `.env`:

```bash
# Copy the example
cp .env.example .env

# Edit as needed
nano .env
```

Available variables (see `.env.example` for complete list):

```bash
# Volume paths (for bind mounts)
REPO_MOUNT_PATH=
REDIS_DATA_PATH=
MEMGRAPH_DATA_PATH=

# Service ports
REDIS_PORT=6379
MEMGRAPH_PORT=7687
API_SSE_PORT=10101
API_HTTP_PORT=10102

# Service configuration
API_LOG_LEVEL=DEBUG
REDIS_PERSISTENCE=yes
MEMGRAPH_MEMORY_LIMIT=1g
```## Service Details

### Base Services (Always Available)

- **redis** (port 6379) - Cache and event streaming
- **memgraph** (port 7687) - Graph database
- **code-graph-http** (port 8000) - Backend HTTP API
- **jupyter** (port 8888) - Jupyter notebook environment

### Optional Services (Depends on Profile)

- **test-db** - Isolated test database instance
- **test-api** - Test-specific API configuration
- Additional services per profile

## Health Checks

All services include health checks. Verify startup:

```bash
docker-compose -f docker-compose.yml ps
```

Expected output:

```text
NAME                  STATE              HEALTH
redis                 Up 2 minutes       (healthy)
memgraph              Up 2 minutes       (healthy)
code-graph-http       Up 1 minute        (healthy)
jupyter               Up 1 minute
```

## Volume Mounts

### Standard Volumes

```yaml
repo-mount:          # Your codebase
redis-data:          # Redis persistence
memgraph-data:       # Memgraph persistence
```

### Custom Volumes (Profile-Specific)

Some profiles may add additional volumes. Check individual profile files for details.

## Environment Variables

### Core Variables (set in compose files)

```bash
REDIS_URL=redis://redis:6379
MEMGRAPH_URL=bolt://memgraph:7687
BACKEND_API_URL=http://code-graph-http:8000
```

### Override Variables (`.env` file)

Create `infrastructure/.env` to override defaults:

```bash
REDIS_PORT=6379
MEMGRAPH_PORT=7687
LOG_LEVEL=DEBUG
```

## Dockerfile Integration

The `Dockerfile` in the root directory supports multi-stage builds:

```dockerfile
FROM python:3.12-slim AS base
FROM base AS development
FROM base AS production
FROM base AS sse
FROM base AS http
```

Compose files reference these via the `target` field:

```yaml
code-graph-http:
  build:
    context: .
    target: http
```

## Common Tasks

### View logs for a specific service

```bash
docker-compose -f docker-compose.yml logs -f memgraph
```

### Scale a service

```bash
docker-compose -f docker-compose.yml up -d --scale jupyter=2
```

### Run a one-off command

```bash
docker-compose -f docker-compose.yml run redis redis-cli ping
```

### Rebuild images

```bash
docker-compose -f docker-compose.yml build --no-cache
```

### Access service shell

```bash
docker-compose -f docker-compose.yml exec code-graph-http bash
```

### Clean everything

```bash
docker-compose -f docker-compose.yml down -v
```

## Troubleshooting

### Services fail to start

```bash
# Check logs
docker-compose -f docker-compose.yml logs

# Verify health
docker-compose -f docker-compose.yml ps

# Rebuild from scratch
docker-compose -f docker-compose.yml down -v
docker-compose -f docker-compose.yml build --no-cache
docker-compose -f docker-compose.yml up
```

### Port conflicts

If ports 6379, 7687, 8000, or 8888 are already in use:

1. Update the port mappings in `docker-compose.yml`
2. Or stop conflicting services: `docker ps` → `docker kill <container>`

### Volume mount issues

Check that paths in compose files are correct and exist on your system.

### In GitHub Codespaces

Use the `profiles/codespaces.yml` which has pre-configured paths:

```bash
docker-compose -f docker-compose.yml -f profiles/codespaces.yml up
```

## Adding New Profiles

To create a new profile:

1. Create `infrastructure/profiles/yourprofile.yml`
2. Include base compose syntax (can be partial overrides)
3. Add to Makefile: `yourprofile-up`, `yourprofile-down`, etc.
4. Document in the table above

---

**Last Updated**: November 15, 2025  
**Branch**: feature/memgraph-integration

