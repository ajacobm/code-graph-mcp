# OpenTelemetry & Observability Specification

**Status**: Proposed  
**Created**: November 15, 2025  
**Branch**: feature/memgraph-integration

## Overview

This specification defines a comprehensive observability stack for Code Graph MCP, enabling real-time monitoring of graph construction, analysis operations, and system health.

**Core Vision**: Watch a codebase spawn into a graph as it's analyzed, with rich telemetry, distributed tracing, and live metrics visualization.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Application Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  MCP Server  │  │  HTTP API    │  │  WebSocket   │          │
│  │   (stdio)    │  │  (FastAPI)   │  │   (SSE)      │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                  │                  │                   │
│         └──────────────────┴──────────────────┘                  │
│                            │                                      │
│                   ┌────────▼────────┐                            │
│                   │  OpenTelemetry  │                            │
│                   │   SDK + Auto-   │                            │
│                   │  Instrumentation│                            │
│                   └────────┬────────┘                            │
└────────────────────────────┼─────────────────────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────▼───────┐ ┌───▼──────┐ ┌────▼─────┐
     │   Jaeger       │ │  Loki    │ │Prometheus│
     │  (Traces)      │ │  (Logs)  │ │ (Metrics)│
     └────────┬───────┘ └───┬──────┘ └────┬─────┘
              │             │             │
              └─────────────┼─────────────┘
                            │
                   ┌────────▼────────┐
                   │     Grafana     │
                   │  (Visualization)│
                   └─────────────────┘
```

## Key Use Cases

### 1. Real-Time Graph Construction Monitoring

**Scenario**: Watch nodes and edges being created as code is analyzed.

**Telemetry**:
- **Traces**: Full span per file analysis (start → parse → extract → graph insert)
- **Metrics**: 
  - `graph.nodes.created` (counter, by language/type)
  - `graph.edges.created` (counter, by relationship_type)
  - `graph.construction.duration_seconds` (histogram)
- **Logs**: Structured JSON with node/edge IDs for correlation
- **Events**: WebSocket broadcasts for UI updates

**Dashboard**: Live graph visualization showing:
- Nodes appearing in real-time
- Rate of construction (nodes/sec, edges/sec)
- Bottlenecks (slow files)
- Language distribution as it evolves

### 2. Query Performance Analysis

**Scenario**: Understand which queries are slow and why.

**Telemetry**:
- **Traces**: Query execution spans (route → cache check → Memgraph → serialize)
- **Metrics**:
  - `query.duration_seconds` (histogram, by query_type)
  - `query.cache_hit_rate` (gauge)
  - `query.result_size` (histogram)
- **Logs**: Query text, parameters, execution plan
- **Exemplars**: Link slow queries to traces

**Dashboard**: Query heatmap, P50/P95/P99 latencies, cache efficiency

### 3. CDC Event Streaming

**Scenario**: Monitor real-time sync between services.

**Telemetry**:
- **Traces**: Event flow (Redis publish → consumer → Memgraph write)
- **Metrics**:
  - `cdc.events.published` (counter, by event_type)
  - `cdc.lag_seconds` (gauge)
  - `cdc.batch_size` (histogram)
- **Logs**: Event payloads for debugging
- **Events**: WebSocket for UI notification

**Dashboard**: CDC lag monitor, event throughput, sync health

### 4. AST Parsing & Language Detection

**Scenario**: Track multi-language parsing performance.

**Telemetry**:
- **Traces**: Per-file parsing (detect language → parse → extract symbols)
- **Metrics**:
  - `ast.parse.duration_seconds` (histogram, by language)
  - `ast.parse.errors` (counter, by language)
  - `ast.symbols_extracted` (histogram, by symbol_type)
- **Logs**: Parse errors with file context
- **Baggage**: Language, file size, complexity

**Dashboard**: Language breakdown, parse error rate, symbol extraction funnel

## Technology Stack

### Core Components

| Component | Technology | Purpose | Port |
|-----------|-----------|---------|------|
| **Tracing** | Jaeger | Distributed traces | 16686 (UI), 4318 (OTLP) |
| **Logging** | Loki | Centralized logs | 3100 |
| **Metrics** | Prometheus | Time-series metrics | 9090 |
| **Visualization** | Grafana | Unified dashboards | 3000 |
| **Exporter** | OpenTelemetry Collector | Telemetry aggregation | 4317 (gRPC), 4318 (HTTP) |

### Python Instrumentation

```toml
[project.dependencies]
opentelemetry-api = "^1.21.0"
opentelemetry-sdk = "^1.21.0"
opentelemetry-instrumentation-fastapi = "^0.42b0"
opentelemetry-instrumentation-redis = "^0.42b0"
opentelemetry-instrumentation-httpx = "^0.42b0"
opentelemetry-exporter-otlp = "^1.21.0"
opentelemetry-instrumentation-logging = "^0.42b0"
opentelemetry-instrumentation-asyncio = "^0.42b0"
```

### Auto-Instrumentation

Leverage OpenTelemetry's auto-instrumentation for:
- FastAPI endpoints (HTTP spans)
- Redis operations (cache spans)
- HTTPX requests (external call spans)
- asyncio tasks (concurrency spans)

## Implementation Plan

### Phase 1: Structured Logging (Foundation)

**Goal**: Replace print statements with structured JSON logging.

**Changes**:

1. **Install structlog**:
```toml
structlog = "^23.2.0"
python-json-logger = "^2.0.7"
```

2. **Configure in `src/code_graph_mcp/logging_config.py`**:
```python
import structlog
import logging
from pythonjsonlogger import jsonlogger

def configure_logging(log_level: str = "INFO", output_format: str = "json"):
    """Configure structured logging for the application."""
    
    if output_format == "json":
        # JSON output for Loki ingestion
        handler = logging.StreamHandler()
        formatter = jsonlogger.JsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s',
            timestamp=True
        )
        handler.setFormatter(formatter)
    else:
        # Human-readable for local dev
        handler = logging.StreamHandler()
        
    logging.basicConfig(
        handlers=[handler],
        level=getattr(logging, log_level.upper())
    )
    
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if output_format == "json"
            else structlog.dev.ConsoleRenderer()
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
```

3. **Usage in code**:
```python
import structlog

logger = structlog.get_logger(__name__)

# Rich contextual logging
logger.info(
    "node_created",
    node_id=node.id,
    node_type=node.type,
    language=node.language,
    file=node.file,
    duration_ms=elapsed * 1000
)

logger.warning(
    "parse_failed",
    file=filepath,
    language=detected_language,
    error=str(e),
    exc_info=True
)
```

**Outcome**: All logs are JSON, ready for Loki ingestion.

### Phase 2: OpenTelemetry Tracing

**Goal**: Add distributed tracing for all operations.

**Changes**:

1. **Initialize OTel SDK** (`src/code_graph_mcp/telemetry.py`):
```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

def init_tracing(service_name: str = "code-graph-mcp"):
    """Initialize OpenTelemetry tracing."""
    resource = Resource(attributes={
        "service.name": service_name,
        "service.version": "1.2.0",
        "deployment.environment": os.getenv("ENVIRONMENT", "development")
    })
    
    provider = TracerProvider(resource=resource)
    
    # Export to OTel Collector
    otlp_exporter = OTLPSpanExporter(
        endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317"),
        insecure=True
    )
    
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    trace.set_tracer_provider(provider)
    
    return trace.get_tracer(__name__)
```

2. **Instrument FastAPI** (`src/code_graph_mcp/server/graph_api.py`):
```python
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

app = FastAPI(title="Code Graph MCP API")

# Auto-instrument all endpoints
FastAPIInstrumentor.instrument_app(app)
```

3. **Manual spans for key operations**:
```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

async def analyze_file(filepath: Path, language: str):
    with tracer.start_as_current_span(
        "analyze_file",
        attributes={
            "file.path": str(filepath),
            "file.language": language,
            "file.size_bytes": filepath.stat().st_size
        }
    ) as span:
        # Parse
        with tracer.start_as_current_span("ast.parse"):
            ast_tree = parse_file(filepath, language)
            span.set_attribute("ast.node_count", count_nodes(ast_tree))
        
        # Extract
        with tracer.start_as_current_span("extract.symbols"):
            symbols = extract_symbols(ast_tree)
            span.set_attribute("symbols.count", len(symbols))
        
        # Graph insert
        with tracer.start_as_current_span("graph.insert"):
            await insert_to_graph(symbols)
        
        return symbols
```

**Outcome**: Full traces from API → parsing → graph insertion.

### Phase 3: Prometheus Metrics

**Goal**: Expose business metrics for alerting and dashboarding.

**Changes**:

1. **Install prometheus_client**:
```toml
prometheus-client = "^0.19.0"
```

2. **Define metrics** (`src/code_graph_mcp/metrics.py`):
```python
from prometheus_client import Counter, Histogram, Gauge, Info

# Graph construction
NODES_CREATED = Counter(
    'graph_nodes_created_total',
    'Total nodes created',
    ['language', 'type']
)

EDGES_CREATED = Counter(
    'graph_edges_created_total',
    'Total edges created',
    ['relationship_type']
)

# Query performance
QUERY_DURATION = Histogram(
    'query_duration_seconds',
    'Query execution time',
    ['query_type', 'cache_status']
)

CACHE_HIT_RATE = Gauge(
    'cache_hit_rate',
    'Cache hit rate (0-1)'
)

# CDC events
CDC_EVENTS_PUBLISHED = Counter(
    'cdc_events_published_total',
    'CDC events published',
    ['event_type']
)

CDC_LAG = Gauge(
    'cdc_lag_seconds',
    'CDC processing lag'
)

# System health
ACTIVE_CONNECTIONS = Gauge(
    'websocket_connections_active',
    'Active WebSocket connections'
)

SERVICE_INFO = Info(
    'service',
    'Service information'
)

SERVICE_INFO.info({
    'version': '1.2.0',
    'environment': os.getenv('ENVIRONMENT', 'dev')
})
```

3. **Instrument code**:
```python
from .metrics import NODES_CREATED, QUERY_DURATION

# In graph construction
NODES_CREATED.labels(language=lang, type=node_type).inc()

# In query handler
with QUERY_DURATION.labels(
    query_type="search_nodes",
    cache_status="hit" if cached else "miss"
).time():
    results = await execute_query(query)
```

4. **Expose metrics endpoint** (FastAPI):
```python
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

@app.get("/metrics")
async def metrics():
    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
```

**Outcome**: Prometheus scrapes `/metrics` endpoint every 15s.

### Phase 4: Loki + Grafana Integration

**Goal**: Centralized log aggregation and visualization.

**Docker Compose Addition** (`infrastructure/profiles/observability.yml`):
```yaml
services:
  # OpenTelemetry Collector (aggregator)
  otel-collector:
    image: otel/opentelemetry-collector-contrib:latest
    command: ["--config=/etc/otel-collector-config.yaml"]
    volumes:
      - ./otel-collector-config.yaml:/etc/otel-collector-config.yaml
    ports:
      - "4317:4317"  # OTLP gRPC
      - "4318:4318"  # OTLP HTTP
      - "8888:8888"  # Prometheus metrics
    depends_on:
      - jaeger
      - loki
      - prometheus

  # Jaeger (distributed tracing)
  jaeger:
    image: jaegertracing/all-in-one:latest
    environment:
      - COLLECTOR_OTLP_ENABLED=true
    ports:
      - "16686:16686"  # UI
      - "14250:14250"  # gRPC

  # Loki (log aggregation)
  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"
    command: -config.file=/etc/loki/local-config.yaml

  # Promtail (log shipper)
  promtail:
    image: grafana/promtail:latest
    volumes:
      - /var/log:/var/log
      - ./promtail-config.yaml:/etc/promtail/config.yaml
    command: -config.file=/etc/promtail/config.yaml

  # Prometheus (metrics storage)
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    ports:
      - "9090:9090"
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.enable-lifecycle'

  # Grafana (visualization)
  grafana:
    image: grafana/grafana:latest
    environment:
      - GF_AUTH_ANONYMOUS_ENABLED=true
      - GF_AUTH_ANONYMOUS_ORG_ROLE=Admin
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
      - ./grafana/dashboards:/var/lib/grafana/dashboards
    ports:
      - "3000:3000"
    depends_on:
      - prometheus
      - loki
      - jaeger

  # Update main service to output JSON logs
  code-graph-http:
    environment:
      - LOG_FORMAT=json
      - OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
      - OTEL_SERVICE_NAME=code-graph-mcp
    labels:
      logging: "promtail"

volumes:
  prometheus-data:
  grafana-data:
```

**Prometheus Config** (`infrastructure/prometheus.yml`):
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'code-graph-mcp'
    static_configs:
      - targets: ['code-graph-http:8000']
    metrics_path: '/metrics'
  
  - job_name: 'otel-collector'
    static_configs:
      - targets: ['otel-collector:8888']
```

**Promtail Config** (`infrastructure/promtail-config.yaml`):
```yaml
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: docker
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        refresh_interval: 5s
        filters:
          - name: label
            values: ["logging=promtail"]
    relabel_configs:
      - source_labels: ['__meta_docker_container_name']
        target_label: 'container'
      - source_labels: ['__meta_docker_container_log_stream']
        target_label: 'stream'
```

**Outcome**: All logs flow to Loki, queryable in Grafana.

### Phase 5: Grafana Dashboards

**Pre-built Dashboards**:

1. **Graph Construction Monitor** (`grafana/dashboards/graph-construction.json`):
   - Line chart: Nodes created/sec (by language)
   - Line chart: Edges created/sec (by type)
   - Stat panel: Total nodes/edges
   - Table: Recent file analyses (from traces)
   - Heatmap: Parse duration distribution

2. **Query Performance** (`grafana/dashboards/query-performance.json`):
   - Heatmap: Query latency by endpoint
   - Line chart: Cache hit rate
   - Table: Slowest queries (with trace links)
   - Stat panel: P95/P99 latencies

3. **CDC Event Streaming** (`grafana/dashboards/cdc-monitor.json`):
   - Line chart: Events published/sec
   - Gauge: Current lag (seconds)
   - Table: Recent events (from Loki)
   - Alert: Lag > 10 seconds

4. **System Health** (`grafana/dashboards/system-health.json`):
   - CPU/Memory usage (from cAdvisor)
   - Active WebSocket connections
   - Error rate by service
   - Redis connection pool stats

**Dashboard Provisioning** (`grafana/provisioning/dashboards/dashboard.yaml`):
```yaml
apiVersion: 1

providers:
  - name: 'Code Graph MCP'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards
```

**Datasource Provisioning** (`grafana/provisioning/datasources/datasource.yaml`):
```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true

  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100

  - name: Jaeger
    type: jaeger
    access: proxy
    url: http://jaeger:16686
```

## Real-Time Graph Visualization

### WebSocket Event Broadcasting

Enhance existing WebSocket support to broadcast telemetry events:

```python
# In graph construction
async def broadcast_node_created(node: Node):
    event = {
        "type": "node_created",
        "data": {
            "id": node.id,
            "name": node.name,
            "type": node.type,
            "language": node.language,
            "file": node.file,
            "timestamp": datetime.now().isoformat()
        },
        "trace_id": trace.get_current_span().get_span_context().trace_id
    }
    await websocket_manager.broadcast(event)
    
    # Also emit metric
    NODES_CREATED.labels(
        language=node.language,
        type=node.type
    ).inc()
```

### Frontend Integration

```typescript
// Frontend: Subscribe to real-time graph construction
const ws = new WebSocket('ws://localhost:8000/ws/graph-events');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'node_created') {
    // Add node to visualization
    graph.addNode({
      id: data.data.id,
      label: data.data.name,
      color: getColorByLanguage(data.data.language),
      trace_id: data.trace_id  // Link to trace in Jaeger
    });
    
    // Update metrics overlay
    updateMetrics({
      totalNodes: graph.nodes().length,
      nodesPerSecond: calculateRate()
    });
  }
};
```

## Alerting

### Prometheus Alerting Rules (`infrastructure/alerts.yml`):

```yaml
groups:
  - name: code_graph_alerts
    interval: 30s
    rules:
      - alert: HighCDCLag
        expr: cdc_lag_seconds > 30
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "CDC lag is high"
          description: "CDC processing is {{ $value }}s behind"
      
      - alert: HighQueryLatency
        expr: histogram_quantile(0.95, query_duration_seconds_bucket) > 5
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Query P95 latency > 5s"
      
      - alert: ParseErrorRateHigh
        expr: rate(ast_parse_errors_total[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High parse error rate"
          description: "{{ $value }} parse errors/sec"
```

## Makefile Targets

Add to `Makefile`:

```makefile
# Observability Targets
observability-up:
	$(COMPOSE_BASE) -f infrastructure/profiles/observability.yml up -d
	@echo "✅ Observability stack started"
	@echo "   Grafana:    http://localhost:3000"
	@echo "   Jaeger:     http://localhost:16686"
	@echo "   Prometheus: http://localhost:9090"

observability-down:
	$(COMPOSE_BASE) -f infrastructure/profiles/observability.yml down

grafana-open:
	open http://localhost:3000

jaeger-open:
	open http://localhost:16686

metrics-check:
	curl -s http://localhost:8000/metrics | head -20
```

## Environment Variables

Add to `.env`:

```bash
# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json  # json or console

# OpenTelemetry
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
OTEL_SERVICE_NAME=code-graph-mcp
OTEL_TRACES_SAMPLER=parentbased_traceidratio
OTEL_TRACES_SAMPLER_ARG=1.0  # 100% sampling in dev

# Prometheus
PROMETHEUS_METRICS_ENABLED=true

# Grafana
GRAFANA_ADMIN_PASSWORD=admin
```

## Benefits

1. **Real-Time Monitoring**: Watch graph construction live in Grafana
2. **Performance Insights**: P95/P99 latencies, bottleneck identification
3. **Error Tracking**: Centralized logs with trace correlation
4. **Alerting**: Proactive notification of issues (CDC lag, high latency)
5. **Debugging**: Full distributed traces from API → parsing → graph insertion
6. **Capacity Planning**: Historical metrics for scaling decisions
7. **User Experience**: WebSocket events for live UI updates

## Migration Path

1. ✅ Phase 1 (Week 1): Structured logging → Loki
2. ✅ Phase 2 (Week 2): OpenTelemetry tracing → Jaeger
3. ✅ Phase 3 (Week 2): Prometheus metrics + `/metrics` endpoint
4. ✅ Phase 4 (Week 3): Docker Compose observability profile
5. ✅ Phase 5 (Week 3): Grafana dashboards + alerting
6. ✅ Phase 6 (Week 4): WebSocket event broadcasting for live UI

## Next Steps

1. Create `infrastructure/profiles/observability.yml`
2. Install Python dependencies (structlog, opentelemetry-*)
3. Add `src/code_graph_mcp/telemetry.py` + `logging_config.py`
4. Instrument key code paths (file analysis, queries, CDC)
5. Build Grafana dashboards
6. Test with `make observability-up` and analyze live

---

**Related Documentation**:
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Production deployment
- [BACKEND_HOSTING_GUIDE.md](BACKEND_HOSTING_GUIDE.md) - API infrastructure
- [SSE.md](../supporting/SSE.md) - WebSocket/SSE implementation
- [REDIS.md](../supporting/REDIS.md) - CDC event streaming

**Last Updated**: November 15, 2025  
**Status**: Ready for implementation

