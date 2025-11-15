# Quick Reference: GHCR + Codespaces

## 🚀 First Time Setup

### 1. Enable GHCR Publishing
```bash
./scripts/setup-ghcr.sh
```

### 2. Make Package Public (One-Time)
1. Visit: https://github.com/ajacobm?tab=packages
2. Click `code-graph-mcp` → Package settings
3. Change visibility to **Public**

## 📦 Available Images

### Backend
```bash
ghcr.io/ajacobm/code-graph-mcp:sse-latest          # SSE server
ghcr.io/ajacobm/code-graph-mcp:stdio-latest        # stdio MCP
ghcr.io/ajacobm/code-graph-mcp:http-latest         # REST API
ghcr.io/ajacobm/code-graph-mcp:production-latest   # Optimized
ghcr.io/ajacobm/code-graph-mcp:development-latest  # Dev mode
```

### Frontend
```bash
ghcr.io/ajacobm/code-graph-mcp-frontend:production-latest   # Prod (serve)
ghcr.io/ajacobm/code-graph-mcp-frontend:development-latest  # Dev (hot reload)
```

### GitHub Pages
```
https://ajacobm.github.io/code-graph-mcp/
```

## 🔧 Development Workflow in Codespaces

### Quick Start
```bash
# 1. Start Redis
./scripts/codespaces-redis.sh

# 2. Run dev server
./scripts/dev-server.sh sse 8000

# 3. Test setup
./scripts/test-codespaces.sh
```

### Using Docker Compose
```bash
# Local build
docker compose -f docker-compose-codespaces.yml up -d

# GHCR images
docker compose -f docker-compose-ghcr.yml up -d

# View logs
docker compose -f docker-compose-codespaces.yml logs -f

# Stop
docker compose -f docker-compose-codespaces.yml down
```

## 🧪 Testing

### Local Testing
```bash
# Health check
curl http://localhost:8000/health

# Redis check
redis-cli ping

# Full test suite
./scripts/test-codespaces.sh
```

### Test MCP Tools
```bash
# Test stdio mode
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | \
  uv run code-graph-mcp --mode stdio
```

## 🔄 CI/CD Pipeline

### Automatic Builds
Triggers on:
- ✅ Push to `main`
- ✅ Pull requests
- ✅ Version tags (`v1.2.3`)
- ✅ Manual dispatch

### Monitor Build
```bash
# Watch latest run
gh run watch

# List recent runs
gh run list --workflow=docker-publish.yml
```

### Manual Trigger
```bash
gh workflow run docker-publish.yml
```

## 📊 Port Forwarding in Codespaces

| Service | Port | Auto-Forward |
|---------|------|--------------|
| SSE Server | 8000 | ✅ Yes |
| HTTP API | 10101 | ✅ Yes |
| Redis | 6379 | ❌ Internal only |

Access forwarded ports in **PORTS** tab.

## 🐛 Common Issues

### "Redis connection refused"
```bash
# Start Redis
./scripts/codespaces-redis.sh

# Or restart
docker restart codegraph-redis
```

### "Port 8000 already in use"
```bash
# Kill process
lsof -ti:8000 | xargs kill -9

# Or use different port
./scripts/dev-server.sh sse 8001
```

### "Permission denied" on scripts
```bash
chmod +x scripts/*.sh
```

### "Can't pull GHCR image"
1. Check package is public
2. Try: `docker pull ghcr.io/ajacobm/code-graph-mcp:sse-latest`
3. View: https://github.com/ajacobm/code-graph-mcp/pkgs/container/code-graph-mcp

## 🎨 Frontend Quick Start

### GitHub Pages (Static Hosting)
```bash
# One-time: Enable in repo settings
# https://github.com/ajacobm/code-graph-mcp/settings/pages
# Source: GitHub Actions

# Access deployed site
https://ajacobm.github.io/code-graph-mcp/
```

### Docker (With Full Stack)
```bash
# Using GHCR images
docker compose -f docker-compose-ghcr.yml up -d

# Access at:
# - Frontend: http://localhost:5173
# - Backend:  http://localhost:10101
```

### Local Development
```bash
cd frontend
npm install
npm run dev

# Access at: http://localhost:5173
```

## 📚 Documentation

- **Frontend Deployment**: [docs/FRONTEND_DEPLOYMENT.md](docs/FRONTEND_DEPLOYMENT.md)
- **Full Infrastructure Guide**: [docs/CODESPACES_INFRASTRUCTURE.md](docs/CODESPACES_INFRASTRUCTURE.md)
- **Deployment Guide**: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **Main README**: [README.md](README.md)

## ⚡ Pro Tips

1. **Fast Iteration**: Use `./scripts/dev-server.sh` for instant reload
2. **Debug Mode**: Add `--verbose` flag to any command
3. **Cache Everything**: Redis improves performance 50-90%
4. **Use GHCR Images**: Skip build time, pull pre-built images
5. **Persistent Redis**: Mount `/workspace/.redis-data` for data persistence

## 🔗 Quick Links

- **Actions**: https://github.com/ajacobm/code-graph-mcp/actions
- **Packages**: https://github.com/ajacobm/code-graph-mcp/pkgs/container/code-graph-mcp
- **Settings**: https://github.com/ajacobm/code-graph-mcp/settings
- **Workflow**: https://github.com/ajacobm/code-graph-mcp/blob/main/.github/workflows/docker-publish.yml
