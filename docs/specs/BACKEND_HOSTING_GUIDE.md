# Backend Hosting & Mixed Environment Guide

## GitHub Pages Limitations (Important!)

### ❌ What GitHub Pages CANNOT Do

GitHub Pages is **static file hosting only**. It:

- ❌ **Cannot run backend services** (no Python, Node.js servers)
- ❌ **Cannot host MCP SSE server** (requires WebSocket/SSE connections)
- ❌ **Cannot host HTTP API** (no server-side code execution)
- ❌ **Cannot connect to databases** (no Redis, PostgreSQL, etc.)
- ❌ **Cannot run background jobs** or cron tasks

### ✅ What GitHub Pages CAN Do

- ✅ **Static HTML/CSS/JS files** - Your built Vue.js app
- ✅ **Client-side routing** - Vue Router with proper config
- ✅ **API calls to external services** - Fetch from other servers
- ✅ **CDN delivery** - Fast global distribution
- ✅ **Custom domains** with HTTPS

### 🎯 The Bottom Line

**GitHub Pages = Frontend Only**

Your Vue.js frontend can be hosted on GitHub Pages, but you **must host the backend elsewhere**:

```
┌─────────────────────────────────────────────────┐
│        GitHub Pages (Static Hosting)            │
│                                                 │
│  ┌───────────────────────────────────────────┐ │
│  │  Vue.js Frontend                          │ │
│  │  (HTML + CSS + JS bundle)                 │ │
│  │                                           │ │
│  │  Connects to external backend via:       │ │
│  │  - https://your-backend.com/api           │ │
│  │  - https://your-backend.com/sse           │ │
│  └───────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
                    │
                    │ HTTPS API calls
                    ▼
┌─────────────────────────────────────────────────┐
│        Backend (Hosted Elsewhere)               │
│                                                 │
│  ┌─────────────┐  ┌──────────────┐            │
│  │ HTTP API    │  │ SSE Server   │            │
│  │ (REST)      │  │ (MCP)        │            │
│  └─────────────┘  └──────────────┘            │
│                                                 │
│  Redis, Database, Background Jobs, etc.        │
└─────────────────────────────────────────────────┘
```

## Backend Hosting Options

### Option 1: Cloud Run (Recommended)

**Perfect for**: Production deployments, auto-scaling

**Providers**:
- **Google Cloud Run** - $0 for first 2M requests/month
- **AWS App Runner** - ~$5/month
- **Azure Container Apps** - $0 for first 180K requests/month

**Setup** (Google Cloud Run):
```bash
# Install gcloud CLI
curl https://sdk.cloud.google.com | bash

# Login
gcloud auth login

# Deploy SSE server
gcloud run deploy code-graph-sse \
  --image ghcr.io/ajacobm/codenav:sse-latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8000 \
  --set-env-vars="REDIS_URL=redis://your-redis-host:6379"

# Deploy HTTP API
gcloud run deploy code-graph-http \
  --image ghcr.io/ajacobm/codenav:http-latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8000

# Get URLs
gcloud run services list
```

**Cost**: ~$0-10/month depending on usage

### Option 2: Fly.io (Easy Docker Deployment)

**Perfect for**: Simple deployment, multiple regions

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Login
flyctl auth login

# Deploy SSE server
flyctl launch --image ghcr.io/ajacobm/codenav:sse-latest \
  --name code-graph-sse \
  --region sea

# Deploy HTTP API
flyctl launch --image ghcr.io/ajacobm/codenav:http-latest \
  --name code-graph-http \
  --region sea

# Add Redis
flyctl redis create

# Get URLs
flyctl status
```

**Cost**: Free tier includes 3 VMs with 256MB RAM

### Option 3: Railway (GitHub Integration)

**Perfect for**: Continuous deployment from GitHub

1. Go to https://railway.app/
2. Connect GitHub repository
3. Select services to deploy:
   - `ghcr.io/ajacobm/codenav:sse-latest`
   - `ghcr.io/ajacobm/codenav:http-latest`
4. Add Redis plugin
5. Set environment variables
6. Deploy!

**Cost**: $5/month for hobby plan

### Option 4: DigitalOcean App Platform

**Perfect for**: Traditional hosting with managed services

```bash
# Install doctl
snap install doctl

# Login
doctl auth init

# Create app spec
cat > app.yaml << 'EOF'
name: codenav
services:
  - name: sse-server
    image:
      registry_type: GHCR
      repository: ajacobm/codenav
      tag: sse-latest
    http_port: 8000
    routes:
      - path: /sse
    envs:
      - key: REDIS_URL
        value: ${redis.DATABASE_URL}
        
  - name: http-api
    image:
      registry_type: GHCR
      repository: ajacobm/codenav
      tag: http-latest
    http_port: 8000
    routes:
      - path: /api

databases:
  - name: redis
    engine: REDIS
EOF

# Deploy
doctl apps create --spec app.yaml
```

**Cost**: $12/month for basic app + $15/month for Redis

### Option 5: Render

**Perfect for**: Simple setup, good free tier

1. Go to https://render.com/
2. New Web Service
3. Docker image: `ghcr.io/ajacobm/codenav:sse-latest`
4. Add Redis
5. Deploy

**Cost**: Free tier available (sleeps after inactivity)

### Option 6: Self-Hosted VPS

**Perfect for**: Full control, cheapest long-term

**Providers**: Hetzner (~$5/mo), Linode ($5/mo), DigitalOcean ($6/mo)

```bash
# SSH into VPS
ssh root@your-vps-ip

# Install Docker
curl -fsSL https://get.docker.com | sh

# Clone repo or use docker-compose
cat > docker-compose.yml << 'EOF'
services:
  redis:
    image: redis:alpine
    volumes:
      - redis-data:/data
      
  sse-server:
    image: ghcr.io/ajacobm/codenav:sse-latest
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
      
  http-api:
    image: ghcr.io/ajacobm/codenav:http-latest
    ports:
      - "10101:8000"
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis

volumes:
  redis-data:
EOF

# Deploy
docker compose up -d

# Set up Caddy for HTTPS
curl https://getcaddy.com | bash -s personal
```

**Cost**: $5-10/month

## Mixed Environments (Local Frontend + Deployed Backend)

### Scenario: Frontend Development with Stable Backend

**Use Case**: Backend is working great, you want to iterate on frontend only.

**Setup**:

1. **Deploy backend to Cloud Run (or any option above)**:
```bash
gcloud run deploy code-graph-http \
  --image ghcr.io/ajacobm/codenav:http-latest \
  --allow-unauthenticated

# Note the URL: https://code-graph-http-xxx-uc.a.run.app
```

2. **Configure frontend to point to deployed backend**:
```bash
cd frontend

# Copy environment template
cp .env.example .env.local-to-deployed

# Edit .env.local-to-deployed
cat > .env.local-to-deployed << 'EOF'
VITE_API_URL=https://code-graph-http-xxx-uc.a.run.app
VITE_SSE_URL=https://code-graph-sse-xxx-uc.a.run.app
VITE_ENV=local-to-deployed
EOF

# Use this env file
cp .env.local-to-deployed .env
```

3. **Run frontend locally**:
```bash
npm run dev
# Access at http://localhost:5173
# Connects to deployed backend!
```

**Benefits**:
- ✅ Fast frontend iteration (hot reload)
- ✅ Stable backend (no need to run locally)
- ✅ Real production data/environment
- ✅ No Docker overhead locally

### Scenario: Backend Development with Deployed Frontend

**Use Case**: Frontend is stable, you want to iterate on backend.

**Setup**:

1. **Deploy frontend to GitHub Pages** (see FRONTEND_DEPLOYMENT.md)

2. **Run backend locally**:
```bash
# Start Redis
./scripts/codespaces-redis.sh

# Run backend with CORS enabled for GitHub Pages
uv run python -m codenav.http_server \
  --port 10101 \
  --cors-origins "https://ajacobm.github.io"
```

3. **Update frontend to point to local backend** (during development):
```typescript
// frontend/src/config.ts
export const API_URL = import.meta.env.DEV 
  ? 'http://localhost:10101' 
  : 'https://your-deployed-backend.com';
```

**Or use Docker backend only**:
```bash
# Start only backend services
docker compose -f docker-compose-backend-only.yml up -d

# Frontend already deployed, just access:
# https://ajacobm.github.io/codenav/
```

## Production Architecture

### Recommended Setup

```
┌────────────────────────────────────────────────────┐
│              GitHub Pages (CDN)                    │
│         https://ajacobm.github.io/...              │
│                                                    │
│  ┌──────────────────────────────────────────────┐ │
│  │         Vue.js Frontend                      │ │
│  │  (Deployed automatically on push to main)    │ │
│  └──────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────┘
                      │
                      │ HTTPS/WSS
                      ▼
┌────────────────────────────────────────────────────┐
│          Cloud Run / Fly.io / Railway              │
│         https://api.yourdomain.com                 │
│                                                    │
│  ┌─────────────────┐    ┌──────────────────────┐  │
│  │  HTTP API       │    │  SSE Server          │  │
│  │  (port 8000)    │    │  (port 8000)         │  │
│  │                 │    │                      │  │
│  │  GHCR Image:    │    │  GHCR Image:         │  │
│  │  http-latest    │    │  sse-latest          │  │
│  └─────────────────┘    └──────────────────────┘  │
│           │                      │                 │
│           └──────────┬───────────┘                 │
│                      ▼                             │
│              ┌──────────────┐                      │
│              │    Redis     │                      │
│              │  (managed)   │                      │
│              └──────────────┘                      │
└────────────────────────────────────────────────────┘
```

**Cost breakdown**:
- GitHub Pages: **Free**
- Cloud Run: ~$5-10/month
- Managed Redis: ~$10-15/month
- **Total**: ~$15-25/month

## Configuration Examples

### Frontend Pointing to Production Backend

```typescript
// frontend/src/config.ts
export const config = {
  apiUrl: import.meta.env.VITE_API_URL || 'https://api.yourdomain.com',
  sseUrl: import.meta.env.VITE_SSE_URL || 'https://sse.yourdomain.com',
  env: import.meta.env.MODE,
};

// Usage in components
import { config } from '@/config';

axios.get(`${config.apiUrl}/graph/nodes`);
```

### Backend with CORS for GitHub Pages

```python
# src/codenav/http_server.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://ajacobm.github.io",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Quick Start: Mixed Environment

### Option 1: Backend in Docker, Frontend Local

```bash
# Start backend services only
docker compose -f docker-compose-backend-only.yml up -d

# Frontend
cd frontend
cp .env.example .env
npm run dev

# Access at http://localhost:5173
# Connects to Docker backend at http://localhost:8000 and :10101
```

### Option 2: Backend on Cloud Run, Frontend Local

```bash
# Deploy backend (one-time)
gcloud run deploy --image ghcr.io/ajacobm/codenav:http-latest

# Frontend
cd frontend
cat > .env << 'EOF'
VITE_API_URL=https://your-cloud-run-url.run.app
EOF

npm run dev
```

### Option 3: Both Deployed, Test Locally

```bash
# Both already deployed
# Frontend: https://ajacobm.github.io/codenav/
# Backend: https://your-cloud-run-url.run.app

# Test locally with same setup
cd frontend
cat > .env << 'EOF'
VITE_API_URL=https://your-cloud-run-url.run.app
EOF

npm run dev
# Matches production environment!
```

## Troubleshooting Mixed Environments

### CORS Errors

**Problem**: Frontend can't connect to backend

**Solution**: Enable CORS on backend

```python
# Add to backend startup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development only!
    # For production, specify exact origins:
    # allow_origins=["https://ajacobm.github.io"],
)
```

### Connection Refused

**Problem**: Backend not accessible

**Solutions**:
```bash
# Check backend is running
curl http://localhost:10101/health

# Check Docker containers
docker ps | grep codegraph

# Check Cloud Run
gcloud run services list
```

### Environment Variable Not Applied

**Problem**: Frontend still uses old API URL

**Solutions**:
```bash
# Restart dev server
cd frontend
npm run dev  # Ctrl+C and restart

# Check environment
cat .env
echo $VITE_API_URL

# Clear Vite cache
rm -rf node_modules/.vite
npm run dev
```

## Summary

### GitHub Pages: Frontend Only
- ✅ Host Vue.js static build
- ❌ Cannot host backend services
- ❌ Cannot host MCP SSE server
- ❌ Cannot run Python/Node.js code

### Backend Hosting: Many Options
1. **Cloud Run** - Recommended for production
2. **Fly.io** - Easy Docker deployment
3. **Railway** - GitHub integration
4. **DigitalOcean** - Traditional hosting
5. **Render** - Good free tier
6. **VPS** - Full control, cheapest

### Mixed Environments: Very Possible!
- ✅ Local frontend + deployed backend
- ✅ Deployed frontend + local backend
- ✅ Docker backend + local frontend
- ✅ Any combination you need!

## Next Steps

1. **Deploy backend** to Cloud Run or Fly.io
2. **Configure frontend** to point to deployed backend
3. **Test mixed environment** locally
4. **Deploy frontend** to GitHub Pages
5. **Monitor** and scale as needed

## Documentation Links

- **Frontend Deployment**: [FRONTEND_DEPLOYMENT.md](FRONTEND_DEPLOYMENT.md)
- **Testing Guide**: [TESTING_GUIDE.md](TESTING_GUIDE.md)
- **Codespaces Guide**: [CODESPACES_INFRASTRUCTURE.md](CODESPACES_INFRASTRUCTURE.md)
- **Quick Reference**: [../GHCR_QUICK_REF.md](../GHCR_QUICK_REF.md)
