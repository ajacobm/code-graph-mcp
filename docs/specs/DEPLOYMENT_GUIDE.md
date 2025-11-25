# CodeNavigator - Deployment Guide

## Quick Start (Docker Compose)

### 1. Start Full Stack
```bash
docker-compose -f docker-compose-multi.yml up -d
```

**Services**:
- **Backend HTTP API** on `localhost:8000` (main service)
- **Frontend UI** on `localhost:5173` (Vue 3 + Vite)
- **SSE Server** on `localhost:10101` (alternative MCP transport)
- **Redis** on `localhost:6379` (caching + CDC streams)
- **Redis Insight** on `localhost:5540` (Redis monitoring)

### 2. Wait for Health Checks
Initial startup takes ~2-3 minutes while the backend analyzes the codebase.

Monitor progress:
```bash
docker logs codenav-code-graph-http-1
```

Wait for: `INFO: Application startup complete`

### 3. Test API

**Health Check**:
```bash
curl http://localhost:8000/health
```

**Graph Statistics**:
```bash
curl http://localhost:8000/api/graph/stats
```

**WebSocket Connection** (Python):
```python
import asyncio
import aiohttp

async def test_ws():
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect('http://localhost:8000/ws/events') as ws:
            msg = await ws.receive_json()
            print(f"Received: {msg}")

asyncio.run(test_ws())
```

## Architecture Overview

### Backend (Python FastAPI + MCP SDK)
- **Entry Point**: `src/codenav/http_server.py`
- **Graph Engine**: `src/codenav/server/analysis_engine.py`
- **CDC Manager**: `src/codenav/cdc_manager.py` (Change Data Capture)
- **WebSocket Server**: `src/codenav/websocket_server.py`

### Event Flow
```
Code Graph Mutation
  ↓
CDCManager.publish_* → Redis Streams + Pub/Sub
  ↓
WebSocketConnectionManager.broadcast
  ↓
Frontend EventsClient receives
  ↓
Vue components (LiveStats, EventLog, AnalysisProgress) update
```

Latency: <100ms from mutation to UI

### Frontend (Vue 3 + TypeScript)
- **Entry Point**: `frontend/src/main.ts`
- **API Client**: `frontend/src/api/graphClient.ts`
- **Events Client**: `frontend/src/api/eventsClient.ts`
- **Real-Time Components**:
  - `LiveStats.vue` - Connection status & counters
  - `AnalysisProgress.vue` - Real-time analysis tracking
  - `EventLog.vue` - CDC event stream visualization

## Deployment Steps

### 1. Build HTTP Server Image
```bash
docker build -t ajacobm/codenav:http -f Dockerfile --target http .
```

### 2. Configure Environment
Create `.compose.env` (or use defaults):
```bash
# Project root to analyze
CODENAV_REPO_MOUNT=/path/to/codebase

# Redis connection
CODENAV_REDIS_URL=redis://redis:6379

# Stack name for docker-compose
STACK_NAME=codenav
```

### 3. Verify Health
```bash
# Check service status
docker-compose -f docker-compose-multi.yml ps

# View HTTP server startup logs
docker logs codenav-code-graph-http-1 | grep -E "startup|initialized|health"

# Test endpoints
curl http://localhost:8000/api/graph/stats
curl http://localhost:5173  # Frontend
```

## Troubleshooting

### HTTP Server Not Starting
**Symptoms**: Health check stays "health: starting" after 2 minutes

**Solution**: 
1. Check logs: `docker logs codenav-code-graph-http-1`
2. Look for `Application startup complete` message
3. Verify Redis is running: `docker logs codenav-redis-1`

**Common Causes**:
- Analysis timeout (5 minute limit in code)
- Redis connection failure
- Missing project files

### WebSocket Connection Failing
**Symptoms**: Frontend shows "disconnected" status, EventLog empty

**Solution**:
1. Check browser console for connection errors
2. Verify endpoint: `curl http://localhost:8000/ws/status`
3. Check server logs: `docker logs codenav-code-graph-http-1`

### Performance Issues
**Monitoring Tools**:
- Redis Insight: `http://localhost:5540`
- Uvicorn logs: `docker logs codenav-code-graph-http-1 | grep -E "GET|POST|ERROR"`
- Container stats: `docker stats codenav-code-graph-http-1`

## Performance Considerations

### Pagination
All list endpoints support pagination to prevent memory overload:
```
/api/graph/query/callers?symbol=main&limit=100&offset=0
/api/graph/query/callees?symbol=main&limit=100&offset=0
/api/graph/query/references?symbol=main&limit=100&offset=0
/api/graph/categories/{category}?limit=20&offset=0
```

### Progressive Disclosure (Frontend)
- ConnectionsList initially shows 20 items
- "Load More" button loads 10 items at a time
- Prevents rendering 300+ DOM nodes for high-degree vertices

### Redis Caching
- Node/relationship lookups cached
- Stream-based CDC ensures no events missed
- Pub/Sub broadcasts instantly to connected clients

## Production Deployment

### Single Server
```bash
# Use production Dockerfile targets
docker build -t codenav:prod -f Dockerfile --target production .

# Run with gunicorn for multiple workers
docker run -p 8000:8000 \
  -e REDIS_URL=redis://redis:6379 \
  codenav:prod \
  gunicorn -w 4 -k uvicorn.workers.UvicornWorker \
  codenav.http_server:app
```

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: code-graph-api
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: api
        image: codenav:prod
        ports:
        - containerPort: 8000
        env:
        - name: REDIS_URL
          value: redis://redis-service:6379
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
```

## Monitoring & Logging

### Key Metrics
```python
# Check analysis stats
curl http://localhost:8000/api/graph/stats

# Monitor WebSocket connections
curl http://localhost:8000/ws/status
```

### Log Levels
```bash
# Standard logs
docker logs codenav-code-graph-http-1

# Tail with follow
docker logs -f codenav-code-graph-http-1

# Filter by level
docker logs codenav-code-graph-http-1 | grep ERROR
```

## Cleanup

### Stop Stack
```bash
docker-compose -f docker-compose-multi.yml down
```

### Remove Volumes
```bash
docker-compose -f docker-compose-multi.yml down -v
```

### Full Cleanup
```bash
docker-compose -f docker-compose-multi.yml down --remove-orphans -v
docker system prune -a
```

## Testing

### Unit Tests
```bash
pytest tests/ -k "not playwright" -v
```

### Integration Tests
```bash
pytest tests/test_http_websocket_integration.py -v
pytest tests/test_cdc_manager.py -v
pytest tests/test_websocket_server.py -v
```

### E2E Tests (Requires Running Stack)
```bash
pytest tests/playwright/test_realtime_features.py -v
```

### Manual WebSocket Test
```bash
python3 << 'EOF'
import asyncio
import aiohttp

async def test():
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect('http://localhost:8000/ws/events') as ws:
            print("Connected!")
            for i in range(5):
                msg = await ws.receive_json()
                print(f"Event {i+1}: {msg}")
            await ws.close()

asyncio.run(test())
EOF
```

## Next Steps

1. **Load Testing**: Benchmark with k6 or locust
2. **Security**: Add authentication/authorization layer
3. **Metrics**: Integrate Prometheus/Grafana for monitoring
4. **Cache Optimization**: Analyze hot paths with Redis profiling
5. **Documentation**: Generate API docs with Swagger/OpenAPI
