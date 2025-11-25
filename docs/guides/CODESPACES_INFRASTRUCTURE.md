# GitHub Codespaces Infrastructure Guide

## Overview

This guide covers running and testing `codenav` in GitHub Codespaces with Redis, including how to work with GitHub Container Registry (GHCR) images.

## Architecture in Codespaces

```
┌─────────────────────────────────────────┐
│        GitHub Codespace (VM)            │
│                                         │
│  ┌──────────────┐    ┌──────────────┐  │
│  │ Redis        │◄───┤ code-graph-  │  │
│  │ Container    │    │ mcp Container│  │
│  │ :6379        │    │ :8000/:10101 │  │
│  └──────────────┘    └──────────────┘  │
│         ▲                    ▲          │
│         │                    │          │
│  ┌──────┴────────────────────┴───────┐ │
│  │   Docker Compose Network          │ │
│  └────────────────────────────────────┘ │
│                                         │
│  Port Forwarding to Local Machine      │
└─────────────────────────────────────────┘
        │
        ▼
   Your Browser / MCP Client
```

## GitHub Container Registry (GHCR) Setup

### 1. Enable Package Publishing

Your GitHub Actions workflow is configured to automatically push to GHCR. No manual setup needed! The workflow runs on:
- Every push to `main`
- Pull requests
- Version tags (`v*.*.*`)
- Manual dispatch

### 2. Image Naming Convention

Images are published to:
```
ghcr.io/ajacobm/codenav:<target>-<version>
```

Available targets:
- `ghcr.io/ajacobm/codenav:development-latest`
- `ghcr.io/ajacobm/codenav:production-latest`
- `ghcr.io/ajacobm/codenav:sse-latest`
- `ghcr.io/ajacobm/codenav:http-latest`
- `ghcr.io/ajacobm/codenav:stdio-latest`

### 3. Make Packages Public (One-Time Setup)

1. Go to https://github.com/ajacobm?tab=packages
2. Click on `codenav`
3. Click **Package settings**
4. Scroll to **Danger Zone** → Change visibility to **Public**

## Running in Codespaces

### Option 1: Local Development (Recommended)

Run directly without Docker for fastest iteration:

```bash
# Start Redis in background
./scripts/codespaces-redis.sh

# Run MCP server in stdio mode
uv run codenav --mode stdio --enable-cache --redis-url redis://localhost:6379

# Or SSE mode with hot reload
uv run codenav --mode sse --host 0.0.0.0 --port 8000 --enable-cache --redis-url redis://localhost:6379 --verbose
```

### Option 2: Docker Compose (Full Stack)

Use the Codespaces-specific compose file:

```bash
# Start everything
docker compose -f docker-compose-codespaces.yml up -d

# View logs
docker compose -f docker-compose-codespaces.yml logs -f

# Stop everything
docker compose -f docker-compose-codespaces.yml down
```

### Option 3: Pull from GHCR

Use pre-built images from your registry:

```bash
# Pull latest SSE image
docker pull ghcr.io/ajacobm/codenav:sse-latest

# Run with Redis
docker compose -f docker-compose-ghcr.yml up -d
```

## Infrastructure Options

### 1. Redis Deployment Options in Codespaces

#### A. Local Redis (Docker Compose) - Recommended
- ✅ **Fastest**: No network latency
- ✅ **Free**: Included in Codespace
- ✅ **Simple**: One command to start
- ⚠️ **Ephemeral**: Data lost when Codespace stops (unless using persistent volume)

```yaml
services:
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes
```

#### B. Redis Cloud (External) - Production Testing
- ✅ **Persistent**: Data survives Codespace restarts
- ✅ **Scalable**: Real production environment
- ⚠️ **Cost**: Paid service (free tier available)
- ⚠️ **Latency**: Network round-trip

Setup:
1. Sign up at https://redis.com/try-free/
2. Create a free database
3. Add to Codespace secrets:
   ```bash
   gh secret set REDIS_URL --body "redis://default:password@redis-12345.cloud.redislabs.com:12345"
   ```
4. Restart Codespace to load secret

#### C. Upstash Redis (Serverless) - Recommended for Production
- ✅ **Serverless**: Pay per request
- ✅ **Persistent**: Durable storage
- ✅ **Free Tier**: 10,000 commands/day
- ✅ **Low Latency**: Edge network

Setup:
1. Sign up at https://upstash.com/
2. Create Redis database
3. Copy the `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN`
4. Add to environment:
   ```bash
   export REDIS_URL="redis://default:YOUR_TOKEN@YOUR_HOST:6379"
   ```

### 2. Port Forwarding

Codespaces automatically forwards ports. Access your services:

| Service | Port | Access URL |
|---------|------|------------|
| MCP SSE Server | 8000 | https://CODESPACE_NAME-8000.app.github.dev |
| MCP SSE Server (alt) | 10101 | https://CODESPACE_NAME-10101.app.github.dev |
| Redis | 6379 | localhost:6379 (not exposed publicly) |

VS Code will show forwarded ports in the **PORTS** tab.

### 3. Testing Your Setup

```bash
# Quick health check
./scripts/test-codespaces.sh

# Test Redis connection
redis-cli ping  # Should return PONG

# Test MCP server (SSE mode)
curl http://localhost:8000/health

# Test MCP server (stdio mode)
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | uv run codenav --mode stdio
```

## Development Workflow

### 1. Make Changes

Edit code in Codespaces editor (VS Code in browser).

### 2. Test Locally

```bash
# Fast iteration - no Docker rebuild
uv run codenav --mode stdio --verbose

# Or with hot reload
uv run codenav --mode sse --host 0.0.0.0 --port 8000 --verbose
```

### 3. Test with Docker (Optional)

```bash
# Rebuild and test
docker compose -f docker-compose-codespaces.yml up --build

# Or test specific target
docker build --target sse -t test-sse .
docker run -p 8000:8000 test-sse
```

### 4. Commit and Push

```bash
git add .
git commit -m "Your changes"
git push origin main
```

### 5. GitHub Actions Builds Automatically

- Workflow triggers on push to `main`
- Builds all 5 targets in parallel
- Pushes to `ghcr.io/ajacobm/codenav:*`
- Takes ~5-10 minutes

### 6. Pull and Use New Images

```bash
# On another machine or clean environment
docker pull ghcr.io/ajacobm/codenav:sse-latest
docker run -p 8000:8000 ghcr.io/ajacobm/codenav:sse-latest
```

## Persistent Storage in Codespaces

Codespaces workspace is persistent, but Docker volumes are not. Options:

### Option A: Use Workspace Directory

Mount `/workspace` directory in containers:

```yaml
volumes:
  - /workspace/.redis-data:/data
```

This persists across Codespace restarts.

### Option B: Use External Redis

See Redis deployment options above.

## Performance Tips

1. **Use Local Redis**: Avoid external Redis during development for speed
2. **Skip Docker**: Run `uv run` directly for fastest iteration
3. **Pre-build Images**: Use GHCR images to skip build time
4. **Use Buildx Cache**: GitHub Actions caches layers between builds

## Troubleshooting

### "Cannot connect to Redis"

```bash
# Check Redis is running
docker ps | grep redis

# Or if using local Redis
redis-cli ping

# Start Redis if needed
docker compose up redis -d
```

### "Port already in use"

```bash
# Kill existing process
lsof -ti:8000 | xargs kill -9

# Or use different port
uv run codenav --mode sse --port 8001
```

### "Docker build fails"

```bash
# Clean build cache
docker system prune -af

# Rebuild with no cache
docker compose build --no-cache
```

### "GitHub Actions can't push to GHCR"

1. Check repository settings → Actions → General
2. Ensure "Read and write permissions" is enabled
3. Re-run the workflow

## Cost Considerations

| Resource | Free Tier | Cost After |
|----------|-----------|------------|
| GitHub Codespaces | 120 core-hours/month | $0.18/hour (2-core) |
| GHCR Storage | 500 MB | $0.25/GB/month |
| GHCR Bandwidth | Unlimited public pulls | N/A |
| Redis (local Docker) | Free | N/A |
| Upstash Redis | 10K commands/day | $0.20/100K commands |

**Recommendation**: Use Codespaces for development, GHCR for distribution, local Redis for dev, Upstash for production.

## Example: Full Development Session

```bash
# 1. Start Redis
docker run -d -p 6379:6379 redis:alpine

# 2. Run MCP server locally
uv run codenav --mode sse --port 8000 --redis-url redis://localhost:6379 --verbose

# 3. In another terminal, test it
curl http://localhost:8000/health

# 4. Make changes to code
# (edit in VS Code)

# 5. Server auto-reloads (if using watchdog)
# Or manually restart

# 6. Test changes
# (use MCP client or curl)

# 7. Commit and push
git add .
git commit -m "Add new feature"
git push

# 8. GitHub Actions builds and pushes to GHCR automatically
# Check: https://github.com/ajacobm/codenav/actions

# 9. Pull and test production image
docker pull ghcr.io/ajacobm/codenav:sse-latest
docker run -p 8000:8000 ghcr.io/ajacobm/codenav:sse-latest
```

## Next Steps

- [ ] Enable GitHub Packages public visibility
- [ ] Set up Codespace secrets for external Redis (optional)
- [ ] Configure devcontainer.json for auto-setup (optional)
- [ ] Add status badge to README showing build status
