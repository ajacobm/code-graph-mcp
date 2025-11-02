# SSE (Server-Sent Events) Support

This document describes the SSE HTTP API support added to the Code Graph MCP Server, allowing you to use the analysis tools via HTTP endpoints instead of the MCP protocol.

## Overview

The SSE server provides HTTP endpoints that expose the same functionality as the MCP server:
- `/list-tools` - GET endpoint returning available analysis tools
- `/call-tool` - POST endpoint with SSE streaming for tool execution

## Running the SSE Server

### Method 1: Using the main script with mode flag

```bash
# Run in SSE mode
code-graph-mcp --mode sse --host 0.0.0.0 --port 8000

# Run in stdio (MCP) mode (default)
code-graph-mcp --mode stdio
```

### Method 2: Using the dedicated SSE script

```bash
# Run the SSE server directly
code-graph-sse --host 0.0.0.0 --port 8000 --debug
```

### Method 3: Using Docker

```bash
# Build and run SSE server
docker build -t code-graph-mcp --target sse .
docker run -p 8000:8000 -v ./your-project:/app/workspace:ro code-graph-mcp

# Or using docker-compose
docker-compose up code-graph-sse

# For development with hot reload
docker-compose --profile dev up code-graph-dev
```

### Method 4: Using uv (development)

```bash
# Install dependencies
uv sync

# Run SSE server
uv run python -m code_graph_mcp.sse_server --port 8000 --debug

# Or run main script in SSE mode
uv run code-graph-mcp --mode sse --port 8000 --verbose
```

## API Endpoints

### GET /

Returns server information and available endpoints.

**Response:**
```json
{
  "name": "Code Graph MCP SSE Server",
  "version": "1.2.3",
  "description": "Server-Sent Events API for code graph intelligence",
  "project_root": "/app/workspace",
  "endpoints": {
    "list_tools": "/list-tools",
    "call_tool": "/call-tool"
  }
}
```

### GET /health

Health check endpoint for monitoring.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": 1703123456.789,
  "analysis_engine_ready": true
}
```

### GET /list-tools

Returns the list of available analysis tools.

**Response:**
```json
[
  {
    "name": "analyze_codebase",
    "description": "🔍 Perform comprehensive codebase analysis...",
    "inputSchema": {
      "type": "object",
      "properties": {
        "rebuild_graph": {
          "type": "boolean",
          "description": "Force rebuild of code graph",
          "default": false
        }
      }
    }
  },
  // ... more tools
]
```

### POST /call-tool

Execute a tool with Server-Sent Events streaming.

**Request Body:**
```json
{
  "name": "analyze_codebase",
  "arguments": {
    "rebuild_graph": false
  }
}
```

**Response:** Server-Sent Events stream with the following event types:

#### Event: start
```
event: start
data: {"tool": "analyze_codebase", "status": "starting"}
```

#### Event: progress
```
event: progress
data: {"status": "executing", "tool": "analyze_codebase"}
```

#### Event: result
```
event: result
data: {"results": ["# Analysis Results\n\n..."], "execution_time": 2.34}
```

#### Event: complete
```
event: complete
data: {"tool": "analyze_codebase", "status": "completed", "execution_time": 2.34}
```

#### Event: error
```
event: error
data: {"error": "Error message", "tool": "analyze_codebase", "traceback": "..."}
```

## Client Examples

### JavaScript/Browser

```javascript
async function callTool(toolName, arguments = {}) {
  const response = await fetch('/call-tool', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      name: toolName,
      arguments: arguments
    })
  });

  const eventSource = new EventSource('/call-tool');
  
  eventSource.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Event:', event.type, 'Data:', data);
  };
  
  eventSource.addEventListener('result', function(event) {
    const result = JSON.parse(event.data);
    console.log('Tool result:', result.results);
  });
  
  eventSource.addEventListener('error', function(event) {
    const error = JSON.parse(event.data);
    console.error('Tool error:', error.error);
    eventSource.close();
  });
  
  eventSource.addEventListener('complete', function(event) {
    console.log('Tool completed');
    eventSource.close();
  });
}

// Usage
callTool('analyze_codebase', { rebuild_graph: false });
```

### Python

```python
import requests
import sseclient
import json

def call_tool(base_url, tool_name, arguments=None):
    url = f"{base_url}/call-tool"
    data = {
        "name": tool_name,
        "arguments": arguments or {}
    }
    
    response = requests.post(url, json=data, stream=True)
    response.raise_for_status()
    
    client = sseclient.SSEClient(response)
    
    for event in client.events():
        data = json.loads(event.data)
        
        if event.event == 'start':
            print(f"Started tool: {data['tool']}")
        elif event.event == 'progress':
            print(f"Progress: {data['status']}")
        elif event.event == 'result':
            print("Results:", data['results'])
            return data['results']
        elif event.event == 'error':
            print(f"Error: {data['error']}")
            return None
        elif event.event == 'complete':
            print(f"Completed in {data['execution_time']:.2f}s")
            break

# Usage
results = call_tool('http://localhost:8000', 'analyze_codebase')
```

### cURL

```bash
# List tools
curl -X GET http://localhost:8000/list-tools

# Call a tool with SSE streaming
curl -X POST http://localhost:8000/call-tool \
  -H "Content-Type: application/json" \
  -d '{"name": "analyze_codebase", "arguments": {}}' \
  --no-buffer
```

## Configuration Options

### Command Line Arguments (SSE Mode)

```bash
code-graph-mcp --mode sse [options]
code-graph-sse [options]
```

Options:
- `--project-root PATH`: Root directory to analyze (default: current directory)
- `--host HOST`: Host to bind to (default: 0.0.0.0)
- `--port PORT`: Port to bind to (default: 8000)
- `--verbose`: Enable debug logging
- `--disable-file-watcher`: Disable automatic file change detection

### Environment Variables

```bash
export CODEGRAPHMCP_LOG_LEVEL=DEBUG
export CODEGRAPHMCP_CACHE_SIZE=500000
export CODEGRAPHMCP_MAX_FILES=10000
export CODEGRAPHMCP_FILE_WATCHER=true
export CODEGRAPHMCP_DEBOUNCE_DELAY=2.0
```

### Docker Environment Variables

```yaml
environment:
  - CODEGRAPHMCP_LOG_LEVEL=INFO
  - CODEGRAPHMCP_FILE_WATCHER=true
  - CODEGRAPHMCP_CACHE_SIZE=300000
```

## Docker Deployment

### Production Deployment

```bash
# Build production image
docker build -t code-graph-mcp --target production .

# Run SSE server
docker run -d \
  --name code-graph-sse \
  -p 8000:8000 \
  -v /path/to/your/code:/app/workspace:ro \
  -e CODEGRAPHMCP_LOG_LEVEL=INFO \
  code-graph-mcp \
  code-graph-mcp --mode sse --host 0.0.0.0 --port 8000
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'
services:
  code-graph-sse:
    build:
      context: .
      target: sse
    ports:
      - "8000:8000"
    volumes:
      - "./your-project:/app/workspace:ro"
    environment:
      - CODEGRAPHMCP_LOG_LEVEL=INFO
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

```bash
# Run
docker-compose up code-graph-sse

# Run in development mode with hot reload
docker-compose --profile dev up code-graph-dev
```

## Integration Examples

### Kubernetes Deployment

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: code-graph-sse
spec:
  replicas: 2
  selector:
    matchLabels:
      app: code-graph-sse
  template:
    metadata:
      labels:
        app: code-graph-sse
    spec:
      containers:
      - name: code-graph-sse
        image: code-graph-mcp:latest
        ports:
        - containerPort: 8000
        env:
        - name: CODEGRAPHMCP_LOG_LEVEL
          value: "INFO"
        volumeMounts:
        - name: workspace
          mountPath: /app/workspace
          readOnly: true
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: workspace
        persistentVolumeClaim:
          claimName: code-workspace-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: code-graph-sse-service
spec:
  selector:
    app: code-graph-sse
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

### Nginx Reverse Proxy

```nginx
# /etc/nginx/sites-available/code-graph-sse
server {
    listen 80;
    server_name code-graph.example.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # SSE specific settings
        proxy_cache off;
        proxy_buffering off;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
    }
}
```

## Performance Considerations

### Caching

The SSE server uses the same LRU caching as the MCP server:
- Tool results are cached for repeated calls
- Analysis results persist until files change
- File watcher automatically invalidates caches on changes

### Scaling

For high-throughput scenarios:
- Run multiple instances behind a load balancer
- Use persistent storage for workspace mounting
- Configure appropriate resource limits
- Monitor memory usage (depends on project size)

### Memory Usage

Typical memory usage:
- Small projects (<100 files): 50-100MB
- Medium projects (100-1000 files): 100-500MB
- Large projects (>1000 files): 500MB-2GB

## Troubleshooting

### Common Issues

1. **Port already in use**: Change the port with `--port 8001`
2. **Permission denied**: Ensure the user has read access to project files
3. **Out of memory**: Reduce cache sizes or increase container memory limits
4. **SSE connection drops**: Check firewall/proxy settings for long-lived connections

### Debug Mode

```bash
# Enable verbose logging
code-graph-sse --debug --verbose

# Check server logs
docker logs code-graph-sse -f
```

### Health Monitoring

```bash
# Check server health
curl http://localhost:8000/health

# Monitor SSE connection
curl -N http://localhost:8000/call-tool \
  -H "Content-Type: application/json" \
  -d '{"name": "project_statistics", "arguments": {}}'
```

## Comparison: SSE vs MCP

| Feature | SSE Server | MCP Server |
|---------|------------|------------|
| Protocol | HTTP/SSE | MCP (stdio) |
| Client Support | Any HTTP client | MCP-compatible clients |
| Real-time Updates | Server-Sent Events | Bidirectional messaging |
| Deployment | Docker, K8s, etc. | Process spawn |
| Scaling | Horizontal scaling | Single process |
| Debugging | HTTP tools | MCP debugging tools |
| Use Case | Web apps, APIs | IDE plugins, AI tools |

Choose SSE for web integrations and HTTP-based systems. Choose MCP for AI tools and IDE plugins that support the MCP protocol.