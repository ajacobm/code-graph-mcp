# Session 19: Memgraph Integration + Jupyter Data Science Environment

**Date**: 2025-11-15  
**Branch**: `main` → `feature/memgraph-integration` (to be created)  
**Status**: 🚧 IN PROGRESS - Planning Phase  
**Goal**: Implement Phase 2 Memgraph integration with event-driven CDC sync + establish Jupyter notebook environment for graph data science

---

## Context from Previous Sessions

**Phase 1 Complete (Sessions 13-14)**: ✅
- Redis Streams CDC infrastructure (CDCManager)
- Redis Pub/Sub real-time notifications
- WebSocket live updates to frontend
- Event-driven architecture foundation established

**What's Next (Phase 2)**:
- Memgraph integration with native stream transformations
- Dual query routing (rustworkx for simple, Memgraph for complex)
- MCP Cypher Resources library (10+ pre-built patterns)
- Jupyter notebooks for graph analytics, community detection, centrality analysis
- Ontology extraction & C4 diagram generation

---

## Architecture Decision: Native Stream Transformations + Python Worker Fallback

### Redis Capabilities Review

Based on `docs/GRAPH_DATABASE_EVALUATION.md`, Redis offers 5 advanced features beyond caching:

1. **Redis Streams** (Message Queuing) ✅ - Currently using for CDC
2. **Redis Pub/Sub** (Real-time Notifications) ✅ - Currently using for WebSocket
3. **Redis Time Series** (Performance Tracking) ⬜ - Future
4. **Redis JSON** (Structured Data) ⬜ - Future (for LLM summaries, metadata)
5. **Redis Search** (Full-Text & Vector) ⬜ - Future (semantic code search)

### Memgraph Sync Strategy

**Primary**: Native stream transformations (lower latency, simpler)
```cypher
CREATE STREAM code_graph_events
TOPICS graph:cdc
TRANSFORM memgraph_stream.parse_json
BATCH_SIZE 100;
```

**Fallback**: Python worker consuming Redis Streams (for debugging, custom logic)
```python
async def memgraph_sync_worker():
    while True:
        messages = await redis.xread({'graph:cdc': last_id}, block=1000)
        # Transform events → Cypher MERGE statements
```

### Query Routing Logic

Route queries to **Memgraph Cypher** when:
- Hop count >3
- Pattern matching required (regex, wildcards)
- Graph algorithms needed (PageRank, community detection, centrality)
- Multi-hop path finding with constraints

Route queries to **rustworkx** when:
- Simple adjacency (find_callers, find_callees)
- Direct neighbors (hops ≤3)
- Single-node properties
- Fast in-memory lookups

---

## Implementation Plan

### Step 1: Docker Compose Services ✅ (Ready to implement)

**File**: `docker-compose-multi.yml`

Add two new services:

1. **Memgraph Platform**:
   - Image: `memgraph/memgraph-platform:latest`
   - Ports: 7687 (Bolt), 3000 (Lab UI)
   - Command: `--stream-enabled=true`
   - Volumes: `memgraph-data:/var/lib/memgraph`
   - Environment: `MEMGRAPH_LOG_LEVEL=WARNING`

2. **Jupyter Data Science Notebook**:
   - Image: `jupyter/datascience-notebook:latest`
   - Port: 8888
   - Volumes: `./notebooks:/home/jovyan/work`
   - Environment: `REDIS_URL`, `MEMGRAPH_URL`, `BACKEND_API_URL`
   - Install: `gremlinpython`, `neo4j`, `networkx`, `matplotlib`, `plotly`, `python-louvain`

### Step 2: Memgraph CDC Sync Worker ✅ (Ready to implement)

**File**: `src/code_graph_mcp/memgraph_sync.py` (NEW)

**Classes**:
- `MemgraphClient` - Bolt protocol connection wrapper
- `NativeStreamTransform` - Setup Memgraph native stream consumption
- `PythonSyncWorker` - Fallback Python-based consumer
- `MemgraphSyncManager` - Orchestrates sync strategy selection

**Features**:
- Subscribe to `graph:cdc` Redis Stream
- Transform CDC events → Cypher MERGE statements
- Handle: `NODE_ADDED`, `RELATIONSHIP_ADDED`, `ANALYSIS_COMPLETE`
- Health check endpoint: `/api/memgraph/status` (sync lag, latency)
- Configurable sync mode: `--memgraph-sync-mode=native|worker|disabled`

### Step 3: Query Router ✅ (Ready to implement)

**File**: `src/code_graph_mcp/graph_query_router.py` (NEW)

**Classes**:
- `HybridGraphQueryEngine` - Route queries to optimal backend
- `QueryComplexityDetector` - Analyze query requirements
- `@simple_query` / `@complex_query` - Decorator-based routing

**Integration**:
- Update `/api/graph/query/*` endpoints to use router
- Add performance logging (rustworkx vs Memgraph comparison)
- Add query plan explanation in responses

### Step 4: MCP Cypher Resources Library ✅ (Ready to implement)

**File**: `src/code_graph_mcp/mcp_cypher_resources.py` (NEW)

**10+ Pre-built Cypher Patterns**:
1. `cypher://entry-to-db-paths` - HTTP endpoint → database operations
2. `cypher://impact-analysis` - What breaks if X changes
3. `cypher://circular-dependencies` - Detect call cycles
4. `cypher://architectural-seams` - High coupling between modules
5. `cypher://god-functions` - High complexity + many callers/callees
6. `cypher://orphan-code` - No callers or callees (dead code)
7. `cypher://authentication-flow` - Entry → auth boundary → session
8. `cypher://error-handling-paths` - Entry → error handlers
9. `cypher://test-coverage-gaps` - Functions without test callers
10. `cypher://api-surface` - All public entry points

**Integration**:
- Register as MCP resources in `src/code_graph_mcp/server/mcp_handlers.py`
- Add Playwright E2E tests in `tests/playwright/test_cypher_resources.py`

### Step 5: Jupyter Notebooks ✅ (Ready to implement)

**Directory**: `notebooks/` (NEW)

**Core Notebooks**:
1. `01_graph_basics.ipynb` - Load, query, visualize with NetworkX
2. `02_centrality_analysis.ipynb` - PageRank, betweenness, degree centrality
3. `03_community_detection.ipynb` - Louvain, label propagation, modularity
4. `04_architectural_patterns.ipynb` - Seams, coupling, hotspots, quality metrics
5. `05_ontology_extraction.ipynb` - Domain vocabulary, metadata aggregation
6. `06_c4_diagram_generation.ipynb` - Generate C4 diagrams from graph views

**Utilities**:
- `notebooks/utils/graph_client.py` - Connection helpers (Redis, Memgraph, API)
- `notebooks/utils/c4_builder.py` - Transform graph queries → C4 diagrams (PlantUML/Structurizr)

**Examples**:
- `notebooks/examples/code_graph_mcp/` - Analysis of this codebase (489 nodes, 4475 edges)
- `notebooks/examples/dotnet_framework/` - Pre-analyzed .NET Framework codebase (TBD)

**Git Strategy**:
- Track: `notebooks/01-06*.ipynb`, `notebooks/utils/`, `notebooks/examples/`
- Ignore: `notebooks/scratch/` (user experiments)

---

## C4 Diagram Generation Strategy

### Ontology Extraction Approach

Use graph queries to aggregate architectural metadata:

1. **Domain Concepts** - Extract from class/function names (NLP clustering)
2. **Layer Boundaries** - Detect from import patterns (UI → Business → Data)
3. **Component Boundaries** - Apply community detection algorithms (Louvain)
4. **External Dependencies** - Identify via seam detection (cross-file/language calls)

### C4 Level Mapping

| C4 Level | Graph Query Strategy |
|----------|---------------------|
| **Context** | Find all external seams (e.g., HTTP clients, message queues, databases) |
| **Container** | Group nodes by deployment unit (Docker service, microservice boundary) |
| **Component** | Apply Louvain community detection to find module clusters |
| **Code** | Show individual nodes/relationships (existing graph visualization) |

### Filtering & Views

Support custom C4 views by filtering:
- By module path (e.g., `src/api/`, `src/domain/`)
- By layer (detected via import analysis)
- By architectural seam (high-coupling boundaries)
- By metadata tags (e.g., `security`, `authentication`, `database`)

---

## Testing Strategy (Playwright-First TDD)

**Per `docs/PLAYWRIGHT_TESTING_GUIDE.md` commitment**:

### Test Files to Create:
1. `tests/test_memgraph_sync.py` - Unit tests for sync worker
2. `tests/test_query_router.py` - Query routing logic
3. `tests/test_cypher_resources.py` - MCP resource registration
4. `tests/playwright/test_memgraph_integration.py` - E2E Memgraph queries
5. `tests/playwright/test_cypher_resources_ui.py` - UI for pre-built patterns

### E2E Test Scenarios:
- Navigate to MCP Resources panel
- Select pre-built Cypher query (e.g., "Find Entry to DB Paths")
- Verify results render with path visualization
- Compare performance: simple query (rustworkx) vs complex (Memgraph)
- Test query routing decisions (inspect query plan in response)

---

## Deliverables Checklist

### Infrastructure (Step 1)
- [ ] Add Memgraph service to `docker-compose-multi.yml`
- [ ] Add Jupyter service to `docker-compose-multi.yml`
- [ ] Create `notebooks/` directory structure
- [ ] Add `.gitignore` entry for `notebooks/scratch/`
- [ ] Test `docker compose up` brings up all services

### Backend (Steps 2-4)
- [ ] `src/code_graph_mcp/memgraph_sync.py` - Sync worker implementation
- [ ] `src/code_graph_mcp/graph_query_router.py` - Hybrid query engine
- [ ] `src/code_graph_mcp/mcp_cypher_resources.py` - 10+ Cypher patterns
- [ ] Update `src/code_graph_mcp/server/graph_api.py` - Integrate query router
- [ ] Update `src/code_graph_mcp/server/mcp_handlers.py` - Register Cypher resources
- [ ] Add `/api/memgraph/status` health check endpoint

### Jupyter Notebooks (Step 5)
- [ ] `notebooks/utils/graph_client.py` - Connection helpers
- [ ] `notebooks/utils/c4_builder.py` - C4 diagram generator
- [ ] `notebooks/01_graph_basics.ipynb` - Basics
- [ ] `notebooks/02_centrality_analysis.ipynb` - Centrality metrics
- [ ] `notebooks/03_community_detection.ipynb` - Module boundaries
- [ ] `notebooks/04_architectural_patterns.ipynb` - Seams, coupling
- [ ] `notebooks/05_ontology_extraction.ipynb` - Domain vocabulary
- [ ] `notebooks/06_c4_diagram_generation.ipynb` - Interactive C4 generation

### Testing (Per TDD Commitment)
- [ ] `tests/test_memgraph_sync.py` - 10+ unit tests
- [ ] `tests/test_query_router.py` - 8+ routing tests
- [ ] `tests/test_cypher_resources.py` - 12+ pattern tests
- [ ] `tests/playwright/test_memgraph_integration.py` - 6+ E2E scenarios
- [ ] `tests/playwright/test_cypher_resources_ui.py` - 5+ UI interaction tests

### Documentation
- [ ] Update `docs/GRAPH_DATABASE_EVALUATION.md` - Mark Phase 2 complete
- [ ] Create `docs/JUPYTER_GUIDE.md` - Data science workflows
- [ ] Create `docs/MEMGRAPH_INTEGRATION.md` - Architecture & deployment
- [ ] Update `CRUSH.md` - Session 19 completion summary
- [ ] Create commit messages following conventional commits

---

## Technical Notes for Haiku

### Existing CDC Infrastructure (Already Working)

**CDC Event Flow**:
```
UniversalGraph mutation → CDCManager.publish_event()
    ↓
Redis Streams (xadd to 'graph:cdc') + Redis Pub/Sub (publish to 'graph:events')
    ↓
WebSocketConnectionManager.broadcast() [for frontend]
    ↓
Frontend Vue components (LiveStats, EventLog, AnalysisProgress)
```

**CDCEvent Types** (from `src/code_graph_mcp/cdc_manager.py`):
- `NODE_ADDED` - Node created in graph
- `RELATIONSHIP_ADDED` - Edge created in graph
- `ANALYSIS_STARTED` - Project analysis begins
- `ANALYSIS_PROGRESS` - Progress update (X of Y files)
- `ANALYSIS_COMPLETE` - Analysis finished

**Redis Stream Key**: `graph:cdc`  
**Redis Pub/Sub Channel**: `graph:events`

### Memgraph Connection Details

**Bolt Protocol**: Port 7687 (Neo4j-compatible driver)  
**Python Driver**: `neo4j` package (works with Memgraph)  
**Lab UI**: Port 3000 (visual query builder)

**Connection String**:
```python
from neo4j import GraphDatabase
driver = GraphDatabase.driver("bolt://memgraph:7687")
```

### Query Routing Decision Tree

```
Query arrives at /api/graph/query/*
    ↓
QueryComplexityDetector analyzes:
    - Hop count requested
    - Pattern matching needed?
    - Graph algorithm needed?
    - Regex/wildcard in filters?
    ↓
If simple (hops ≤3, no patterns, no algorithms):
    → rustworkx_graph.find_callers(symbol)  # <1ms
    
If complex (hops >3 OR patterns OR algorithms):
    → memgraph.query(cypher_statement)  # 10-50ms
    
Return: {result, backend_used, execution_time_ms}
```

### Cypher Pattern Examples

**Entry to DB Paths**:
```cypher
MATCH path = (entry:Function {is_entry_point: true})
            -[:CALLS*1..15]->
            (db:Function)
WHERE db.name =~ '.*(insert|update|delete|save|query|execute).*'
RETURN path, length(path) as hops
ORDER BY hops
LIMIT 20
```

**Impact Analysis**:
```cypher
MATCH (changed:Function {name: $symbol})
MATCH (impacted:Function)-[:CALLS*1..10]->(changed)
RETURN impacted.name, 
       impacted.file,
       length(path) as distance
ORDER BY distance
```

**God Functions** (refactoring targets):
```cypher
MATCH (god:Function)
WHERE god.complexity > 15
WITH god, 
     size((god)<-[:CALLS]-()) as caller_count,
     size((god)-[:CALLS]->()) as callee_count
WHERE caller_count + callee_count > 20
RETURN god.name, god.complexity, caller_count, callee_count
ORDER BY god.complexity DESC
```

### Jupyter Notebook Helper Pattern

```python
# notebooks/utils/graph_client.py
import redis.asyncio as redis
from neo4j import GraphDatabase
import httpx

class GraphDataClient:
    def __init__(self):
        self.redis = redis.from_url("redis://redis:6379")
        self.memgraph = GraphDatabase.driver("bolt://memgraph:7687")
        self.api = httpx.AsyncClient(base_url="http://code-graph-http:8000")
    
    async def get_graph_stats(self):
        return await self.api.get("/api/graph/stats")
    
    async def run_cypher(self, query, **params):
        with self.memgraph.session() as session:
            return session.run(query, **params).data()
```

---

## Known Limitations & Future Work

### Session 19 Scope
- Focus on Memgraph sync + query routing + Jupyter setup
- Pre-built Cypher patterns (10+) as MCP Resources
- Basic C4 diagram generation from community detection

### Future Sessions (20+)
- Redis Search for semantic code search (vector embeddings)
- Redis JSON for LLM-generated summaries/annotations
- Redis Time Series for performance tracking over time
- Advanced C4 views with layer detection & custom metadata
- MCP Prompts library (natural language workflows)
- Query performance analytics dashboard

---

## MCP Tools Available

Per `.mcp.json`:
- ✅ **cipher** - Available at `npx cipher --mode mcp` (aggregator mode, OpenRouter API)
- ✅ **playwright** - Browser automation for E2E testing
- ✅ **context7** - Context management
- ✅ **@21st-dev/magic** - AI magic tools
- ✅ **tavily-mcp** - Web search
- ✅ **obsidian** - Knowledge base integration

**Note**: cipher tool can help with Cypher query generation/validation during MCP Resource implementation.

---

## Current System State

**Last Docker Compose Command**: 
```bash
docker compose -f docker-compose-codespaces.yml up -d --build
Exit Code: 1
```

**Likely Issue**: Need to check logs to see what failed. Possible causes:
- Port conflicts (6379, 8000, 5173)
- Build errors in one of the services
- Missing environment variables
- Volume mount issues

**Next Step**: Check logs with:
```bash
docker compose -f docker-compose-codespaces.yml logs
```

---

## Session 19 Status: Ready for Haiku 4.5

**Context Prepared**: ✅
- Architecture decisions documented
- Implementation plan detailed (6 steps, 30+ deliverables)
- Technical notes for CDC, Memgraph, query routing, Jupyter
- Testing strategy aligned with Playwright-first TDD
- Known limitations scoped

**CRUSH.md**: ⏳ Needs update with Session 19 pointer

**Handoff Notes**:
1. Start with Step 1 (docker-compose updates)
2. Test each service independently before integration
3. Follow TDD: Write Playwright tests before implementing features
4. Use cipher MCP tool for Cypher query validation
5. Keep session document updated with progress/blockers

---

**Session Lead**: Sonnet 4.5 → **Haiku 4.5** (handoff in progress)

