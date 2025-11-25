# Build & Deploy Guide for CodeNavigator with docker-compose-multi.yml

## ✅ Yes, the Build Command Gets You What You Need

```bash
docker build -t ajacobm/codenav:sse --target sse .
```

This is the **correct and recommended** approach for building with `docker-compose-multi.yml`.

---

## Why This Works

### Multi-Stage Dockerfile Structure
```
Dockerfile has 4 stages:
1. base           → Common dependencies
2. production     → Inherits from base, installs package
3. sse            → Inherits from production, SSE mode
4. stdio          → Inherits from production, stdio mode
```

### The `--target sse` Flag
- Tells Docker to **stop at the `sse` stage**
- Builds: base → production → sse
- Sets default CMD to: `codenav --mode sse --host 0.0.0.0 --port 8000 --enable-cache`
- Results in image: `ajacobm/codenav:sse`

### docker-compose-multi.yml Configuration
```yaml
services:
  code-graph-codegraphmcp-sse:
    image: ajacobm/codenav:sse  # ← Uses our built image
    ports:
      - "10101:8000"                    # ← HTTP endpoint
    environment:
      - REDIS_URL=redis://redis:6379   # ← Redis for caching
    depends_on:
      - redis                           # ← Start Redis first
    command: >                          # ← Overrides Dockerfile CMD
      uv run codenav
      --mode sse
      --redis-url redis://redis:6379
      --project-root /app/workspace
      --host 0.0.0.0
      --port 8000
      --verbose
```

---

## Complete Build & Deploy Workflow

### Step 1: Build the Image
```bash
cd /mnt/c/Users/ADAM/GitHub/codenav

# Build with SSE stage (recommended with --target)
docker build -t ajacobm/codenav:sse --target sse .

# OR without --target (also works, builds to stdio by default at end)
# docker build -t ajacobm/codenav:sse .
```

### Step 2: Verify Build Succeeded
```bash
docker images | grep codenav
# Should show: ajacobm/codenav  sse
```

### Step 3: Start Services with docker-compose
```bash
# Start Redis + CodeNavigator
docker-compose -f docker-compose-multi.yml up

# Or in background
docker-compose -f docker-compose-multi.yml up -d
```

### Step 4: Verify Services Are Running
```bash
# Check containers
docker-compose -f docker-compose-multi.yml ps

# Expected output:
# NAME                              STATUS
# codenav-redis-1            Up (healthy)
# codenav-code-graph-codegraphmcp-sse-1  Up (healthy)
```

### Step 5: Test the Endpoint
```bash
# Test health endpoint
curl http://localhost:10101/health

# Should return:
# {"status": "healthy", ...}

# Or with MCP tools (if using SSE endpoint):
# http://localhost:10101/sse - SSE endpoint for client connections
# http://localhost:10101/messages - JSON-RPC endpoint for messages
```

### Step 6: View Logs
```bash
# Follow logs from all services
docker-compose -f docker-compose-multi.yml logs -f

# Or specific service
docker-compose -f docker-compose-multi.yml logs -f code-graph-codegraphmcp-sse

# You should see (with your fixes):
# ✅ No "ignore_patterns" file watcher error
# ✅ "Found N functions/classes/imports using AST-Grep"
# ✅ Actual node counts instead of "0 nodes"
```

---

## Architecture: How It All Fits Together

```
┌─ Your Machine ─────────────────────────────────────────┐
│                                                        │
│  http://localhost:10101                               │
│           ↓                                            │
│  ┌──────────────────────────────────────────────┐    │
│  │ Docker Container 1: CodeNavigator (SSE)    │    │
│  │ - Port 10101 → 8000 (internal)               │    │
│  │ - Mode: SSE (HTTP + SSE streaming)           │    │
│  │ - Workspace: /app/workspace                  │    │
│  │ - Can call Redis for caching                 │    │
│  └──────────────────────────────────────────────┘    │
│           ↓ (REDIS_URL=redis://redis:6379)           │
│  ┌──────────────────────────────────────────────┐    │
│  │ Docker Container 2: Redis Cache             │    │
│  │ - Port 6379 (internal network)               │    │
│  │ - Data: /.redis-docker/codegraphmcp          │    │
│  └──────────────────────────────────────────────┘    │
│                                                        │
└────────────────────────────────────────────────────────┘
```

---

## Comparison: Different Build Scenarios

### Scenario 1: Build for SSE (What You Need) ✅
```bash
docker build -t ajacobm/codenav:sse --target sse .
docker-compose -f docker-compose-multi.yml up
```
- Result: HTTP SSE server on port 10101
- Redis: Enabled automatically
- Use for: MCP clients connecting to HTTP endpoint

### Scenario 2: Build for Stdio (Alternative)
```bash
docker build -t ajacobm/codenav:stdio --target stdio .
docker-compose -f docker-compose-multi.yml up
```
- Result: Stdio MCP server (different compose needed)
- Redis: Not used
- Use for: Claude Desktop, other MCP clients using stdio

### Scenario 3: Build for Development
```bash
docker build -t codenav:dev --target development .
```
- Result: Development environment with all extras
- Use for: Development and testing

---

## Troubleshooting

### Issue: Container exits immediately
```bash
# Check logs
docker-compose -f docker-compose-multi.yml logs code-graph-codegraphmcp-sse

# Common causes:
# 1. Port already in use: docker ps | grep 10101
# 2. Redis not running: docker-compose -f docker-compose-multi.yml up redis
# 3. Image build failed: docker build -t ajacobm/codenav:sse --target sse .
```

### Issue: Health check failing
```bash
# Check health endpoint directly
curl -v http://localhost:10101/health

# Check container logs
docker-compose -f docker-compose-multi.yml logs code-graph-codegraphmcp-sse | tail -50
```

### Issue: Redis connection refused
```bash
# Verify Redis is running
docker-compose -f docker-compose-multi.yml logs redis

# Check Redis connectivity from code-graph container
docker-compose -f docker-compose-multi.yml exec code-graph-codegraphmcp-sse redis-cli -h redis ping
# Should return: PONG
```

---

## Quick Reference Commands

```bash
# Build
docker build -t ajacobm/codenav:sse --target sse .

# Start
docker-compose -f docker-compose-multi.yml up

# Stop
docker-compose -f docker-compose-multi.yml down

# Rebuild and restart
docker build -t ajacobm/codenav:sse --target sse . && \
  docker-compose -f docker-compose-multi.yml up --force-recreate

# Test
curl http://localhost:10101/health

# View logs (follow)
docker-compose -f docker-compose-multi.yml logs -f

# Clean up
docker-compose -f docker-compose-multi.yml down -v
```

---

## Summary

✅ **Yes**, `docker build -t ajacobm/codenav:sse --target sse .` gives you exactly what you need for `docker-compose-multi.yml`:

1. **Builds** the production SSE image
2. **Includes** your AST-Grep parsing fixes
3. **Sets up** HTTP/SSE endpoints
4. **Enables** Redis caching automatically
5. **Integrates** perfectly with docker-compose-multi.yml

Just run:
```bash
docker build -t ajacobm/codenav:sse --target sse . && \
docker-compose -f docker-compose-multi.yml up
```

And you're ready to test with your fixes! 🚀
