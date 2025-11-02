# Frontend Docker Deployment

## Development Container

Use the included `Dockerfile` for development with Node 22 (fixes the version issue).

### Build
```bash
docker build -f frontend/Dockerfile -t code-graph-frontend:dev .
```

### Run (Development)
```bash
docker run -it --rm \
  -p 5173:5173 \
  -v $(pwd)/frontend:/app \
  -v /app/node_modules \
  code-graph-frontend:dev
```

The dev server will be available at `http://localhost:5173`

Changes to source files will trigger hot reload automatically.

## Production Container

Use `Dockerfile.prod` for optimized production builds.

### Build
```bash
docker build -f frontend/Dockerfile.prod -t code-graph-frontend:prod .
```

### Run (Production)
```bash
docker run -d --rm \
  -p 5173:5173 \
  code-graph-frontend:prod
```

## Docker Compose (Recommended)

The easiest way is using Docker Compose which includes backend, frontend, Redis, and monitoring:

```bash
# Start entire stack (backend + frontend + Redis + Redis Insight)
docker-compose -f docker-compose-multi.yml up

# Services will be available at:
# Frontend: http://localhost:5173
# Backend: http://localhost:8000
# Redis Insight: http://localhost:5540
```

### Stop Stack
```bash
docker-compose -f docker-compose-multi.yml down
```

### View Logs
```bash
docker-compose -f docker-compose-multi.yml logs -f frontend
docker-compose -f docker-compose-multi.yml logs -f code-graph-sse
```

## Troubleshooting

### "Port 5173 already in use"
Change the port mapping:
```bash
docker run -p 3000:5173 code-graph-frontend:dev
```
Then access at `http://localhost:3000`

### Hot reload not working
Ensure you mount the frontend directory:
```bash
-v $(pwd)/frontend:/app
```

### Build cache issues
Force rebuild without cache:
```bash
docker build --no-cache -f frontend/Dockerfile -t code-graph-frontend:dev .
```

### Check container logs
```bash
docker logs <container-id>
docker logs -f <container-id>  # Follow logs
```

## Environment Variables

The frontend container respects:
- `VITE_API_URL` - Backend API URL (default: http://localhost:8000)
- `NODE_ENV` - "development" or "production"

In Docker Compose, these are set automatically.

## Networking

When using Docker Compose:
- Frontend connects to backend at `http://code-graph-sse:8000`
- From host machine, backend is at `http://localhost:8000`
- Frontend accessible at `http://localhost:5173`

## Node Version

Both Dockerfiles use Node 22-alpine which:
- ✅ Fixes Vite version compatibility issues
- ✅ Is lightweight (Alpine Linux)
- ✅ Has full npm/node support
- ✅ No need for nvm locally

## Performance

Production build includes:
- Code splitting
- Minification
- Tree shaking
- Asset optimization

Typical build size: ~200KB gzipped

## Development Workflow

1. Make changes in `frontend/src/`
2. Dev server automatically recompiles (HMR)
3. Browser auto-refreshes
4. No rebuild needed unless you change config

## Building for Production

If building locally (requires Node 20+):
```bash
cd frontend
npm install
npm run build
npm run preview  # Test production build
```

Or use Docker:
```bash
docker build -f frontend/Dockerfile.prod -t code-graph-frontend:prod .
docker run -p 5173:5173 code-graph-frontend:prod
```
