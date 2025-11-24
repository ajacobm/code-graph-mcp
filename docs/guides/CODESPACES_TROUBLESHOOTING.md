# Codespaces Container & Environment Management

## Overview

GitHub Codespaces uses **devcontainers** to define the development environment. When you have environment issues (missing tools, wrong versions, etc.), you need to either fix the devcontainer config or create manual setup scripts.

## Problem: "uv not found" or Missing Tools

### Solution 1: Rebuild Container (Recommended)

**When**: After updating `.devcontainer/devcontainer.json`

```bash
# In VS Code
# Press: Cmd/Ctrl + Shift + P
# Type: "Codespaces: Rebuild Container"
# Select and wait ~5-10 minutes
```

**Or via GitHub UI**:
1. Go to https://github.com/codespaces
2. Find your codespace
3. Click ⋯ → Delete
4. Create new codespace

### Solution 2: Manual Setup (Quick Fix)

**When**: You don't want to wait for rebuild

```bash
# Install uv manually
pip install uv

# Install dependencies
uv sync --all-extras --dev

# Test
./scripts/test-codespaces.sh
```

### Solution 3: Run Setup Script

```bash
# Run the devcontainer setup script manually
bash .devcontainer/setup.sh
```

## Devcontainer Configuration

### What We've Created

**File**: `.devcontainer/devcontainer.json`

**Features**:
- ✅ Python 3.12 base image
- ✅ Docker-in-Docker support
- ✅ Node.js 22 for frontend
- ✅ GitHub CLI (`gh`)
- ✅ Automatic port forwarding (5173, 8000, 10101, 6379)
- ✅ VS Code extensions pre-installed
- ✅ Post-create setup script

**File**: `.devcontainer/setup.sh`

**What it does**:
1. Installs `uv`
2. Syncs Python dependencies
3. Installs frontend dependencies
4. Makes scripts executable
5. Creates data directories

### How It Works

```
┌────────────────────────────────────────────────────┐
│         Create Codespace (first time)              │
│                      │                             │
│                      ▼                             │
│         Pull base image (python:3.12)              │
│                      │                             │
│                      ▼                             │
│         Install features (docker, node, gh)        │
│                      │                             │
│                      ▼                             │
│         Run postCreateCommand                      │
│         (.devcontainer/setup.sh)                   │
│                      │                             │
│                      ▼                             │
│         ✅ Ready to code!                          │
└────────────────────────────────────────────────────┘
```

## Common Codespace Issues

### Issue 1: Missing Python Tool (uv, pytest, etc.)

**Symptoms**:
```bash
$ uv --version
bash: uv: command not found
```

**Fix**:
```bash
# Quick fix
pip install uv

# Or rebuild container
# Cmd/Ctrl + Shift + P → "Codespaces: Rebuild Container"
```

### Issue 2: Dependencies Not Installed

**Symptoms**:
```bash
$ python -c "import codenav"
ModuleNotFoundError: No module named 'codenav'
```

**Fix**:
```bash
# Install dependencies
uv sync --all-extras --dev

# Or use pip
pip install -e .

# Test
python -c "import codenav; print('✅ Works!')"
```

### Issue 3: Redis Not Running

**Symptoms**:
```bash
$ redis-cli ping
Could not connect to Redis at 127.0.0.1:6379: Connection refused
```

**Fix**:
```bash
# Start Redis
./scripts/codespaces-redis.sh

# Or manually
docker run -d --name codegraph-redis -p 6379:6379 redis:alpine
```

### Issue 4: Docker Not Available

**Symptoms**:
```bash
$ docker ps
Cannot connect to the Docker daemon
```

**Fix**:
```bash
# Check Docker-in-Docker feature is enabled
cat .devcontainer/devcontainer.json | grep docker-in-docker

# Rebuild container if missing
# Cmd/Ctrl + Shift + P → "Codespaces: Rebuild Container"
```

### Issue 5: Port Forwarding Not Working

**Symptoms**:
- Can't access http://localhost:8000
- Frontend can't connect to backend

**Fix**:
```bash
# Check ports in VS Code
# View → Ports panel (should show forwarded ports)

# Or manually forward
# Cmd/Ctrl + Shift + P → "Forward a Port"
# Enter: 8000, 5173, 10101

# Check if service is running
curl http://localhost:8000/health
```

### Issue 6: Out of Storage

**Symptoms**:
```bash
$ docker build ...
no space left on device
```

**Fix**:
```bash
# Clean Docker
docker system prune -af

# Clean Python cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
rm -rf .pytest_cache

# Clean npm cache
cd frontend && rm -rf node_modules && npm ci
```

### Issue 7: Slow Performance

**Symptoms**:
- Codespace feels sluggish
- Commands take too long

**Fix**:
```bash
# Check machine type
# Go to https://github.com/codespaces
# Click ⋯ on your codespace → Change machine type
# Select: 4-core 16GB RAM (recommended)

# Or use fewer Docker containers
# Stop unnecessary services
docker stop $(docker ps -q)
```

## Azure Container Registry MCP Integration

Since you have an Azure tenant with a storage account, here's how to integrate Azure MCP:

### Option 1: Azure Container Registry (ACR)

**Instead of GHCR**, you can use ACR:

```bash
# Install Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Login
az login --tenant YOUR_TENANT_ID

# Create container registry
az acr create \
  --resource-group YOUR_RG \
  --name codegraphmcp \
  --sku Basic

# Login to ACR
az acr login --name codegraphmcp

# Tag and push images
docker tag codenav:sse codegraphmcp.azurecr.io/codenav:sse-latest
docker push codegraphmcp.azurecr.io/codenav:sse-latest
```

**Update workflows**:
```yaml
# .github/workflows/docker-publish.yml
env:
  REGISTRY: codegraphmcp.azurecr.io
  IMAGE_NAME: codenav
```

### Option 2: Azure Container Apps

**Deploy directly from GHCR to Azure**:

```bash
# Create container app
az containerapp create \
  --name code-graph-sse \
  --resource-group YOUR_RG \
  --environment YOUR_ENV \
  --image ghcr.io/ajacobm/codenav:sse-latest \
  --target-port 8000 \
  --ingress external \
  --min-replicas 0 \
  --max-replicas 1

# Deploy HTTP API
az containerapp create \
  --name code-graph-http \
  --resource-group YOUR_RG \
  --environment YOUR_ENV \
  --image ghcr.io/ajacobm/codenav:http-latest \
  --target-port 8000 \
  --ingress external
```

### Option 3: Azure MCP Server Extension

**Enable Azure MCP in VS Code**:

1. Install extension: `ms-azuretools.vscode-azure-mcp-server`
2. Configure in `.vscode/settings.json`:

```json
{
  "azure-mcp": {
    "subscriptionId": "YOUR_SUBSCRIPTION_ID",
    "storageAccount": "YOUR_STORAGE_ACCOUNT",
    "containerRegistry": "codegraphmcp.azurecr.io"
  }
}
```

3. Update MCP config to use Azure:

```json
{
  "mcpServers": {
    "codenav-azure": {
      "type": "streamableHttp",
      "url": "https://code-graph-sse.YOUR_REGION.azurecontainerapps.io/mcp"
    }
  }
}
```

## Best Practices

### 1. Always Commit Devcontainer Changes

```bash
git add .devcontainer/
git commit -m "Add devcontainer configuration"
git push
```

### 2. Test Setup Script Locally

```bash
# Test the setup script works
bash .devcontainer/setup.sh

# Should complete without errors
```

### 3. Document Custom Setup

Create `DEVELOPMENT.md`:

```markdown
## Development Setup

### Codespaces
1. Open in GitHub Codespaces
2. Wait for automatic setup (~3-5 min)
3. Run `./scripts/test-codespaces.sh`

### Local (with devcontainer)
1. Install Docker Desktop
2. Install VS Code + Remote-Containers extension
3. Open folder in VS Code
4. "Reopen in Container" when prompted
```

### 4. Use Codespaces Secrets

```bash
# Set secret via gh CLI
gh secret set AZURE_SUBSCRIPTION_ID --body "xxx"
gh secret set AZURE_TENANT_ID --body "xxx"

# Or via GitHub UI
# https://github.com/settings/codespaces
```

Access in Codespace:
```bash
echo $AZURE_SUBSCRIPTION_ID
```

### 5. Prebuilds (Faster Startup)

Configure in GitHub repo settings:

1. Settings → Codespaces → Prebuilds
2. Enable for `main` branch
3. Set trigger: "On push"
4. First startup: ~10 min
5. Future startups: ~30 seconds! 🚀

## Troubleshooting Workflow

```bash
# 1. Check what's missing
./scripts/test-codespaces.sh

# 2. Install missing tools
pip install uv
uv sync

# 3. Test again
./scripts/test-codespaces.sh

# 4. If still broken, rebuild container
# Cmd/Ctrl + Shift + P → "Codespaces: Rebuild Container"

# 5. Create new codespace if all else fails
# Delete old one, create fresh
```

## When to Rebuild vs Manual Fix

| Issue | Manual Fix | Rebuild Container |
|-------|-----------|-------------------|
| Missing Python package | ✅ `pip install` | ❌ Overkill |
| Missing system tool | ❌ Complex | ✅ Add to devcontainer |
| Wrong Node version | ❌ Hard to change | ✅ Update devcontainer |
| Redis not running | ✅ `./scripts/redis.sh` | ❌ Not needed |
| Out of space | ✅ `docker prune` | ❌ Won't help |
| Corrupt environment | ❌ Hard to diagnose | ✅ Clean slate |

## Quick Reference

```bash
# Test environment
./scripts/test-codespaces.sh

# Fix missing uv
pip install uv && uv sync

# Fix missing dependencies
uv sync --all-extras --dev

# Start Redis
./scripts/codespaces-redis.sh

# Clean up
docker system prune -af

# Rebuild (in VS Code)
# Cmd/Ctrl + Shift + P → "Codespaces: Rebuild Container"
```

## Azure Integration Example

Complete example with Azure MCP:

```bash
# 1. Deploy to Azure Container Apps
az containerapp create \
  --name codenav \
  --resource-group codegraph-rg \
  --environment codegraph-env \
  --image ghcr.io/ajacobm/codenav:sse-latest \
  --target-port 8000 \
  --ingress external \
  --registry-server ghcr.io \
  --registry-username ajacobm \
  --registry-password $GHCR_TOKEN

# 2. Get URL
az containerapp show \
  --name codenav \
  --resource-group codegraph-rg \
  --query properties.configuration.ingress.fqdn \
  --output tsv

# 3. Update MCP config with Azure URL
cat > .mcp.json << 'EOF'
{
  "mcpServers": {
    "codenav-azure": {
      "type": "streamableHttp",
      "url": "https://codenav.YOUR_REGION.azurecontainerapps.io/mcp"
    }
  }
}
EOF
```

## Documentation Links

- **Devcontainer Spec**: https://containers.dev/
- **GitHub Codespaces Docs**: https://docs.github.com/en/codespaces
- **Azure Container Apps**: https://learn.microsoft.com/azure/container-apps/
- **Azure MCP**: https://learn.microsoft.com/azure/ai/
