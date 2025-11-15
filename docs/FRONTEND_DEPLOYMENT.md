# Frontend Deployment Guide

## Overview

The **code-graph-mcp frontend** is a Vue.js 3 application with Vite, TailwindCSS, and Cytoscape for graph visualization. We've set up **three deployment options**:

1. **GitHub Pages** - Free static hosting at `https://ajacobm.github.io/code-graph-mcp/`
2. **GHCR Docker Images** - Containerized frontend for orchestration
3. **Local Development** - Fast iteration in Codespaces or locally

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Repository                         │
│                  ajacobm/code-graph-mcp                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Push to main (frontend/** changes)                         │
│           │                                                  │
│           ├─────────────────┬────────────────────────────┐  │
│           ▼                 ▼                            ▼  │
│  ┌─────────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ GitHub Pages    │  │ GHCR Dev     │  │ GHCR Prod    │  │
│  │ Workflow        │  │ Image        │  │ Image        │  │
│  │                 │  │              │  │              │  │
│  │ Build & Deploy  │  │ node:22      │  │ node:22      │  │
│  │ Static Site     │  │ + Hot Reload │  │ + serve      │  │
│  └─────────────────┘  └──────────────┘  └──────────────┘  │
│           │                 │                            │  │
│           ▼                 ▼                            ▼  │
│  ┌─────────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ GitHub Pages    │  │ GHCR         │  │ GHCR         │  │
│  │ (Free CDN)      │  │ Development  │  │ Production   │  │
│  │                 │  │ Image        │  │ Image        │  │
│  └─────────────────┘  └──────────────┘  └──────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Deployment Options

### 1. GitHub Pages (Recommended for Static Hosting)

**Perfect for**: Public demos, documentation, marketing site

**URL**: `https://ajacobm.github.io/code-graph-mcp/`

**Features**:
- ✅ **Free** hosting with unlimited bandwidth
- ✅ **Global CDN** for fast loading worldwide
- ✅ **HTTPS** enabled by default
- ✅ **Custom domain** support
- ✅ **Automatic** builds on push

**Setup** (One-Time):

```bash
# 1. Enable GitHub Pages
# Go to: https://github.com/ajacobm/code-graph-mcp/settings/pages
# Source: GitHub Actions
# Click "Save"

# 2. Push to main (workflow will trigger automatically)
git add .
git commit -m "Enable GitHub Pages"
git push origin main

# 3. Wait ~2 minutes for deployment
# Visit: https://ajacobm.github.io/code-graph-mcp/
```

**How it works**:
- Workflow: `.github/workflows/deploy-pages.yml`
- Triggers on: Push to `main` with changes in `frontend/**`
- Build time: ~1-2 minutes
- Deployment: Automatic to GitHub Pages

**Limitations**:
- ⚠️ **Static only** - No backend API (use external API)
- ⚠️ **Public repo required** for free hosting
- ⚠️ **1 GB** size limit for site

### 2. GHCR Docker Images (Orchestration)

**Perfect for**: Development, testing, production deployments with backend

**Images**:
- `ghcr.io/ajacobm/code-graph-mcp-frontend:development-latest`
- `ghcr.io/ajacobm/code-graph-mcp-frontend:production-latest`

**Features**:
- ✅ **Full stack** - Frontend + Backend together
- ✅ **Multi-architecture** - AMD64 + ARM64
- ✅ **Development mode** - Hot reload for coding
- ✅ **Production mode** - Optimized build with `serve`

**Quick Start**:

```bash
# Pull and run development image
docker pull ghcr.io/ajacobm/code-graph-mcp-frontend:development-latest
docker run -p 5173:5173 ghcr.io/ajacobm/code-graph-mcp-frontend:development-latest

# Or use docker-compose with full stack
docker compose -f docker-compose-ghcr.yml up -d

# Access at: http://localhost:5173
```

**With Backend** (Full Stack):

```bash
# Starts: Redis + Backend (SSE + HTTP) + Frontend
docker compose -f docker-compose-ghcr.yml up -d

# Access:
# - Frontend: http://localhost:5173
# - SSE API:  http://localhost:8000
# - HTTP API: http://localhost:10101
# - Redis:    localhost:6379 (internal)
```

### 3. Local Development (Fastest)

**Perfect for**: Active development, debugging, rapid iteration

```bash
# Navigate to frontend
cd frontend

# Install dependencies (first time only)
npm install

# Start dev server with hot reload
npm run dev

# Access at: http://localhost:5173
```

**With Backend** (Manual):

```bash
# Terminal 1: Start Redis
./scripts/codespaces-redis.sh

# Terminal 2: Start backend HTTP API
uv run python -m code_graph_mcp.http_server --port 10101

# Terminal 3: Start frontend
cd frontend && npm run dev

# Access at: http://localhost:5173
```

**With Backend** (Docker Compose):

```bash
# Start full stack with local builds
docker compose -f docker-compose-codespaces.yml up -d

# Frontend with hot reload
cd frontend
npm run dev

# Access at: http://localhost:5173
```

## GitHub Pages Configuration

### Enable GitHub Pages

1. Go to: https://github.com/ajacobm/code-graph-mcp/settings/pages
2. **Source**: Select "GitHub Actions"
3. Click **Save**
4. Push to `main` to trigger deployment

### Configure Base URL (if needed)

If your repo name is not the root path, update `vite.config.ts`:

```typescript
export default defineConfig({
  base: '/code-graph-mcp/', // Add this line
  plugins: [vue()],
  // ...
})
```

### Custom Domain

1. Add `CNAME` file to `frontend/public/`:
   ```
   your-domain.com
   ```

2. Configure DNS:
   ```
   Type: CNAME
   Name: www (or @)
   Value: ajacobm.github.io
   ```

3. Enable in settings:
   https://github.com/ajacobm/code-graph-mcp/settings/pages

## Docker Configuration

### Development Mode

**Dockerfile**: `frontend/Dockerfile`

```dockerfile
FROM node:22-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

**Features**:
- Hot module replacement (HMR)
- Source maps for debugging
- Instant updates on file changes

**Usage**:
```bash
docker build -f frontend/Dockerfile -t frontend-dev ./frontend
docker run -p 5173:5173 -v $(pwd)/frontend:/app frontend-dev
```

### Production Mode

**Dockerfile**: `frontend/Dockerfile.prod`

```dockerfile
# Build stage
FROM node:22-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage
FROM node:22-alpine
WORKDIR /app
RUN npm install -g serve
COPY --from=builder /app/dist ./dist
EXPOSE 5173
CMD ["serve", "-s", "dist", "-l", "5173"]
```

**Features**:
- Optimized build (~50% smaller)
- Static file serving with `serve`
- No dev dependencies
- Production-ready caching

**Usage**:
```bash
docker build -f frontend/Dockerfile.prod -t frontend-prod ./frontend
docker run -p 5173:5173 frontend-prod
```

## CI/CD Workflows

### Docker Build Workflow

**File**: `.github/workflows/docker-publish.yml`

**Builds**:
- `ghcr.io/ajacobm/code-graph-mcp-frontend:development-latest`
- `ghcr.io/ajacobm/code-graph-mcp-frontend:production-latest`
- Version tags: `v1.2.3-development`, `v1.2.3-production`

**Triggers**:
- Push to `main`
- Pull requests
- Version tags (`v*.*.*`)
- Manual dispatch

**Build Matrix**:
```yaml
strategy:
  matrix:
    target: [development, production]
```

### GitHub Pages Workflow

**File**: `.github/workflows/deploy-pages.yml`

**Steps**:
1. Checkout repository
2. Setup Node.js 22
3. Install dependencies with `npm ci`
4. Build with `npm run build`
5. Upload `dist/` folder
6. Deploy to GitHub Pages

**Triggers**:
- Push to `main` with changes in `frontend/**`
- Manual dispatch

**Deployment Time**: ~1-2 minutes

## Environment Variables

### Build-time Variables

Configure in `vite.config.ts` or `.env`:

```bash
# .env (for local development)
VITE_API_URL=http://localhost:10101
VITE_SSE_URL=http://localhost:8000
```

### Runtime Variables (Docker)

```bash
# docker-compose.yml or docker run
environment:
  - VITE_API_URL=http://code-graph-http:8000
```

### GitHub Pages (Static)

For GitHub Pages, API URLs must be absolute:

```typescript
// src/config.ts
export const API_URL = import.meta.env.VITE_API_URL || 'https://api.your-backend.com'
```

## Port Configuration

| Environment | Frontend Port | Backend Port | Redis Port |
|-------------|--------------|--------------|------------|
| Local Dev | 5173 | 10101 | 6379 |
| Docker Compose | 5173 | 8000 (SSE), 10101 (HTTP) | 6379 |
| GitHub Pages | N/A (CDN) | External API | N/A |
| Codespaces | 5173 (forwarded) | 8000, 10101 | 6379 |

## Testing

### Local Testing

```bash
cd frontend

# Run dev server
npm run dev

# Build and preview production
npm run build
npm run preview

# Access at: http://localhost:5173
```

### Docker Testing

```bash
# Test development image
docker build -f frontend/Dockerfile -t test-dev ./frontend
docker run -p 5173:5173 test-dev

# Test production image
docker build -f frontend/Dockerfile.prod -t test-prod ./frontend
docker run -p 5173:5173 test-prod

# Test with full stack
docker compose -f docker-compose-codespaces.yml up
```

### GitHub Pages Testing

```bash
# Test Pages build locally
cd frontend
npm run build

# Serve locally
npx serve -s dist -l 5173

# Or use Python
python3 -m http.server 5173 --directory dist
```

## Troubleshooting

### GitHub Pages Not Deploying

**Check workflow status**:
```bash
gh run list --workflow=deploy-pages.yml
gh run view --log
```

**Common issues**:
1. GitHub Pages not enabled in repo settings
2. Branch protection preventing deployments
3. Build errors in workflow logs

**Fix**:
```bash
# Enable GitHub Pages
# https://github.com/ajacobm/code-graph-mcp/settings/pages

# Check permissions
# Settings → Actions → General → Workflow permissions
# Enable: Read and write permissions
```

### Frontend Can't Connect to Backend

**Docker Compose**:
```bash
# Check backend is running
docker ps | grep codegraph

# Check backend logs
docker logs codegraph-http

# Check network connectivity
docker exec codegraph-frontend curl http://code-graph-http:8000/health
```

**Local Development**:
```bash
# Check backend is accessible
curl http://localhost:10101/health

# Check CORS configuration in backend
# Ensure backend allows frontend origin
```

### Port Already in Use

```bash
# Find process using port 5173
lsof -ti:5173

# Kill it
lsof -ti:5173 | xargs kill -9

# Or use different port
npm run dev -- --port 5174
```

### Build Fails

```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Clear Vite cache
rm -rf node_modules/.vite

# Try fresh build
npm run build
```

## Performance Optimization

### GitHub Pages

- ✅ **CDN**: Global edge locations
- ✅ **Gzip**: Automatic compression
- ✅ **Caching**: Browser caching headers
- ✅ **HTTPS**: SSL/TLS by default

**Build optimizations** (automatic with Vite):
- Code splitting
- Tree shaking
- Minification
- Asset optimization

### Docker Production

**Tips**:
1. Use `Dockerfile.prod` for production
2. Multi-stage build reduces image size by ~50%
3. `serve` is lightweight and production-ready
4. Enable gzip compression in `serve`

**Optimize build**:
```bash
# Check bundle size
npm run build -- --report

# Analyze dependencies
npm install -g source-map-explorer
source-map-explorer dist/assets/*.js
```

## Cost Analysis

| Deployment | Cost | Bandwidth | Storage |
|------------|------|-----------|---------|
| GitHub Pages | **Free** | Unlimited | 1 GB |
| GHCR Images | ~$0.25/mo | Unlimited (public) | ~500 MB |
| Codespaces | Free tier | N/A | Workspace storage |

**Total**: ~$0.25/month for everything!

## Next Steps

1. **Enable GitHub Pages**: https://github.com/ajacobm/code-graph-mcp/settings/pages
2. **Push to main**: Trigger deployments
3. **Test locally**: `npm run dev` in `frontend/`
4. **Access GitHub Pages**: https://ajacobm.github.io/code-graph-mcp/
5. **Pull GHCR images**: `docker pull ghcr.io/ajacobm/code-graph-mcp-frontend:production-latest`

## Documentation Links

- **Main README**: [README.md](../README.md)
- **Codespaces Guide**: [CODESPACES_INFRASTRUCTURE.md](CODESPACES_INFRASTRUCTURE.md)
- **GHCR Quick Ref**: [GHCR_QUICK_REF.md](../GHCR_QUICK_REF.md)
- **Setup Checklist**: [SETUP_CHECKLIST.md](../SETUP_CHECKLIST.md)
- **Frontend Dev Guide**: [frontend/DEV_GUIDE.md](../frontend/DEV_GUIDE.md)
