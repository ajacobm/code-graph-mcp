# 🚀 Complete GHCR + Codespaces Setup - Step-by-Step Guide

## ✅ What We've Built

### 1. GitHub Actions CI/CD Pipeline
- **File**: `.github/workflows/docker-publish.yml`
- **Features**:
  - Builds 5 Docker targets in parallel (development, production, sse, http, stdio)
  - Multi-architecture support (AMD64 + ARM64)
  - Automatic tagging with semver, branch names, and SHA
  - BuildKit caching for faster builds
  - Build attestation for security
- **Triggers**: Push to main, PRs, version tags, manual dispatch

### 2. Docker Compose Configurations
- **docker-compose-codespaces.yml**: For development in Codespaces with local builds
- **docker-compose-ghcr.yml**: For using pre-built GHCR images

### 3. Helper Scripts
- **scripts/codespaces-redis.sh**: Start Redis in Codespaces
- **scripts/dev-server.sh**: Quick development server launcher
- **scripts/test-codespaces.sh**: Comprehensive test suite
- **scripts/setup-ghcr.sh**: One-time GHCR setup automation

### 4. Documentation
- **docs/CODESPACES_INFRASTRUCTURE.md**: Complete infrastructure guide
- **GHCR_QUICK_REF.md**: Quick reference card
- **GHCR_INFRASTRUCTURE_OVERVIEW.md**: Architecture diagrams and details
- **README.md**: Updated with GHCR usage instructions

## 📋 First-Time Setup Checklist

### Step 1: Enable GitHub Actions Permissions ⚙️
```bash
# 1. Visit your repository settings
https://github.com/ajacobm/code-graph-mcp/settings/actions

# 2. Under "Workflow permissions", select:
☑️ Read and write permissions
☑️ Allow GitHub Actions to create and approve pull requests

# 3. Click "Save"
```

### Step 2: Trigger First Build 🏗️
```bash
# Option A: Push to main (automatic)
git add .
git commit -m "Add GHCR CI/CD pipeline"
git push origin main

# Option B: Manual trigger
gh workflow run docker-publish.yml

# Monitor build
gh run watch
```

### Step 3: Make Package Public 🌐
```bash
# After first build completes:

# 1. Go to your packages
https://github.com/ajacobm?tab=packages

# 2. Click on "code-graph-mcp"

# 3. Click "Package settings" (right sidebar)

# 4. Scroll to "Danger Zone"

# 5. Click "Change visibility" → "Public"

# 6. Confirm by typing the package name
```

### Step 4: Test in Codespaces 🧪
```bash
# 1. Start Redis
./scripts/codespaces-redis.sh

# 2. Run test suite
./scripts/test-codespaces.sh

# 3. Start development server
./scripts/dev-server.sh sse 8000

# 4. In another terminal, test it
curl http://localhost:8000/health
```

### Step 5: Pull and Test GHCR Image 📦
```bash
# Pull latest SSE image
docker pull ghcr.io/ajacobm/code-graph-mcp:sse-latest

# Run it
docker run -p 8000:8000 ghcr.io/ajacobm/code-graph-mcp:sse-latest

# Test
curl http://localhost:8000/health
```

## 🔄 Daily Development Workflow

### Morning Routine
```bash
# 1. Start Codespace (automatic if configured)

# 2. Start Redis
./scripts/codespaces-redis.sh

# 3. Start dev server with hot reload
./scripts/dev-server.sh sse 8000
```

### Development Loop
```bash
# 1. Edit code in VS Code

# 2. Test automatically reloads (if using dev-server.sh)
#    Or manually restart: Ctrl+C then re-run

# 3. Test changes
curl http://localhost:8000/health

# 4. Run specific tests
pytest tests/test_specific.py -v
```

### Commit and Deploy
```bash
# 1. Commit changes
git add .
git commit -m "Add new feature"

# 2. Push to trigger CI/CD
git push origin main

# 3. Monitor build
gh run watch

# 4. Once complete, pull new image
docker pull ghcr.io/ajacobm/code-graph-mcp:sse-latest
```

## 🎯 Common Tasks

### Start Everything with Docker Compose
```bash
# Using local build
docker compose -f docker-compose-codespaces.yml up -d

# Using GHCR images
docker compose -f docker-compose-ghcr.yml up -d

# View logs
docker compose -f docker-compose-codespaces.yml logs -f

# Stop
docker compose -f docker-compose-codespaces.yml down
```

### Run Without Docker (Fastest)
```bash
# Make sure Redis is running
./scripts/codespaces-redis.sh

# Run directly with uv
uv run code-graph-mcp --mode sse --port 8000 --redis-url redis://localhost:6379 --verbose
```

### Test Production Image Locally
```bash
# Pull production image
docker pull ghcr.io/ajacobm/code-graph-mcp:production-latest

# Run with Redis
docker run -d --name redis redis:alpine
docker run -p 8000:8000 --link redis \
  -e REDIS_URL=redis://redis:6379 \
  ghcr.io/ajacobm/code-graph-mcp:production-latest
```

### Debug Build Issues
```bash
# View workflow runs
gh run list --workflow=docker-publish.yml

# View specific run
gh run view 123456789 --log

# Re-run failed job
gh run rerun 123456789

# Check Docker build locally
docker build --target sse -t test-sse .
```

## 📊 Monitoring

### Build Status
```bash
# Watch current build
gh run watch

# List recent builds
gh run list --workflow=docker-publish.yml --limit 10

# View build details
gh run view --web
```

### Image Status
```bash
# List all images
gh api /users/ajacobm/packages/container/code-graph-mcp/versions

# View package page
https://github.com/ajacobm/code-graph-mcp/pkgs/container/code-graph-mcp

# Pull statistics (via GitHub UI)
https://github.com/ajacobm/code-graph-mcp/pkgs/container/code-graph-mcp
```

### Runtime Status
```bash
# Check Redis
redis-cli ping

# Check containers
docker ps

# Check server health
curl http://localhost:8000/health

# View logs
docker logs codegraph-sse -f
```

## 🐛 Troubleshooting Guide

### Build Failures

**"Permission denied to push to GHCR"**
```bash
# Check Actions permissions
https://github.com/ajacobm/code-graph-mcp/settings/actions

# Ensure "Read and write permissions" is enabled
```

**"Docker build failed"**
```bash
# Check Dockerfile syntax
docker build --target development -t test .

# View detailed logs
gh run view --log
```

### Runtime Issues

**"Cannot connect to Redis"**
```bash
# Check Redis is running
docker ps | grep redis

# Start if needed
./scripts/codespaces-redis.sh

# Test connection
redis-cli ping
```

**"Port 8000 already in use"**
```bash
# Find and kill process
lsof -ti:8000 | xargs kill -9

# Or use different port
./scripts/dev-server.sh sse 8001
```

**"Image pull fails"**
```bash
# Check package is public
https://github.com/ajacobm/code-graph-mcp/pkgs/container/code-graph-mcp

# Try manual pull
docker pull ghcr.io/ajacobm/code-graph-mcp:sse-latest

# Check Docker login (if private)
docker login ghcr.io -u ajacobm
```

## 💡 Pro Tips

1. **Fast Iteration**: Use `./scripts/dev-server.sh` instead of Docker during development
2. **Cache Hits**: Redis caching improves performance 50-90%
3. **Parallel Builds**: GitHub Actions builds all 5 targets simultaneously
4. **Multi-arch**: Images work on Intel and ARM (M1/M2 Macs)
5. **Persistent Data**: Mount `/workspace/.redis-data` for Redis persistence
6. **Hot Reload**: Development target supports code changes without restart
7. **Logs**: Use `docker compose logs -f` for real-time log streaming

## 📚 Additional Resources

- **Infrastructure Guide**: [docs/CODESPACES_INFRASTRUCTURE.md](docs/CODESPACES_INFRASTRUCTURE.md)
- **Quick Reference**: [GHCR_QUICK_REF.md](GHCR_QUICK_REF.md)
- **Architecture**: [GHCR_INFRASTRUCTURE_OVERVIEW.md](GHCR_INFRASTRUCTURE_OVERVIEW.md)
- **Main README**: [README.md](README.md)

## 🎉 Success Indicators

✅ GitHub Actions workflow runs successfully
✅ All 5 images publish to GHCR
✅ Package is publicly accessible
✅ Images pull and run locally
✅ Redis connects successfully
✅ Health endpoint returns 200 OK
✅ MCP tools work in Codespaces

## 🔗 Quick Links

- **Actions Dashboard**: https://github.com/ajacobm/code-graph-mcp/actions
- **Packages**: https://github.com/ajacobm/code-graph-mcp/pkgs/container/code-graph-mcp
- **Repository Settings**: https://github.com/ajacobm/code-graph-mcp/settings
- **Workflow File**: [.github/workflows/docker-publish.yml](.github/workflows/docker-publish.yml)

---

**Need Help?** Check the troubleshooting section or review the detailed infrastructure guide.
