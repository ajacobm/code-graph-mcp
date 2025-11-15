# Graph Database Architecture: Memgraph + Event-Driven Pipeline

**Decision**: Adopting Memgraph as queryable graph database with event-driven sync from Rustworkx via Redis Streams.

**Architecture**: Hybrid model - Rustworkx for fast parsing, Memgraph for powerful Cypher queries, Redis Streams for CDC.

---

## Current Architecture (Redis + Rustworkx)

### What We Have
```
Parse Code → UniversalGraph (rustworkx in-memory) → Redis (cache serialized nodes/edges)
                                ↓
                    Query via Python methods (find_callers, find_callees)
```

**Pros**:
- Fast in-memory graph operations (rustworkx is Rust-based)
- Redis provides persistence and cache hits
- Simple architecture, no additional infrastructure
- Good for <10K node graphs

**Cons**:
- Custom query logic (can't leverage graph query languages)
- No built-in graph algorithms beyond rustworkx
- Limited to in-memory size
- Hard to do complex multi-hop queries
- No ACID guarantees for graph mutations

---

## Redis Beyond Caching: Advanced Capabilities

### 1. **Redis Streams** (Message Queuing)
**Use Case**: Real-time graph updates, event sourcing

```python
# Publish graph mutation events
await redis.xadd('graph:mutations', {
    'event': 'node_added',
    'node_id': 'function:/path/file.py:foo:42',
    'timestamp': time.time()
})

# Consume in frontend via WebSocket
async for message in redis.xread({'graph:mutations': '$'}):
    # Push to connected browsers
    await websocket.send_json(message)
```

**Benefits**:
- Live graph updates in UI without polling
- Event sourcing for undo/replay
- Audit log of all graph changes

### 2. **Redis Pub/Sub** (Real-time Notifications)
**Use Case**: Notify frontend when analysis completes, LLM generates summaries

```python
# Backend publishes analysis completion
await redis.publish('analysis:complete', json.dumps({
    'nodes': 489,
    'relationships': 4475,
    'duration_ms': 1234
}))

# Frontend subscribes
pubsub = redis.pubsub()
await pubsub.subscribe('analysis:complete')
async for message in pubsub.listen():
    # Update UI without polling
```

**Benefits**:
- Real-time UI updates
- No HTTP polling overhead
- Decoupled services

### 3. **Redis Time Series** (Performance Tracking)
**Use Case**: Track analysis performance over time, cache hit rates

```python
# Record analysis metrics
await redis.ts().add('analysis:duration', timestamp, duration_ms)
await redis.ts().add('cache:hit_rate', timestamp, hit_rate)

# Query trends
last_hour = await redis.ts().range('analysis:duration', from_time='-1h')
```

**Benefits**:
- Built-in downsampling and aggregation
- Query historical performance
- Identify performance regressions

### 4. **Redis JSON** (Structured Data Storage)
**Use Case**: Store complex analysis results, user preferences

```python
# Store analysis metadata as JSON
await redis.json().set('analysis:metadata', Path.root_path(), {
    'project_type': 'microservice',
    'languages': ['Python', 'TypeScript'],
    'frameworks': ['FastAPI', 'Vue'],
    'quality_score': 0.87
})

# Query with JSONPath
frameworks = await redis.json().get('analysis:metadata', '$.frameworks')
```

**Benefits**:
- No JSON serialization overhead
- JSONPath queries
- Atomic updates on nested fields

### 5. **Redis Search** (Full-Text & Vector Search)
**Use Case**: Search node names, docstrings, code snippets

```python
# Create index
await redis.ft('nodes').create_index([
    TextField('name'),
    TextField('docstring'),
    TextField('code'),
    TagField('language'),
    NumericField('complexity')
])

# Full-text search
results = await redis.ft('nodes').search('authentication AND jwt')

# Vector search (for semantic code search with embeddings)
embedding = get_code_embedding(query)
results = await redis.ft('nodes').search(
    Query('*=>[KNN 10 @embedding $vec]')
    .dialect(2)
)
```

**Benefits**:
- Native full-text search (no Elasticsearch needed)
- Semantic code search with embeddings
- Fast fuzzy matching

---

## RedisGraph (Now EOL) ❌

**Note**: RedisGraph was discontinued in 2023 and merged into Redis Stack. It used Cypher query language.

**Why EOL**: 
- Redis pivoted away from native graph support
- Recommended migration path: Neo4j or other specialized graph DBs
- Redis JSON + Search can handle simple graph queries, but not native graph

**Impact for Us**: 
- Can't use RedisGraph for Cypher queries
- Must choose between:
  1. Keep rustworkx + Redis cache (current)
  2. Migrate to Neo4j/Memgraph for native graph queries

---

## Neo4j: Industry Standard Graph Database

### What Neo4j Offers

**1. Cypher Query Language** (Powerful & Expressive)
```cypher
// Find all paths from HTTP endpoint to database query
MATCH path = (entry:Function {is_entry_point: true})
             -[:CALLS*1..10]->
             (db:Function)
WHERE db.name CONTAINS 'execute' OR db.name CONTAINS 'query'
RETURN path, length(path) as hops
ORDER BY hops
LIMIT 10

// Find circular dependencies
MATCH (n:Function)-[:CALLS*]->(n)
RETURN n.name, length(path) as cycle_length

// Find code smells (God functions calling many others)
MATCH (god:Function)-[c:CALLS]->()
WITH god, count(c) as call_count
WHERE call_count > 20
RETURN god.name, call_count
ORDER BY call_count DESC
```

**2. Built-in Graph Algorithms**
- **Shortest Path**: Find call chain between any two functions
- **PageRank**: Identify most influential functions
- **Community Detection**: Find modules/clusters
- **Betweenness Centrality**: Find critical functions (like our articulation points)
- **Path Finding**: All paths, weighted paths, k-shortest paths

**3. ACID Compliance**
- Atomic graph mutations
- Consistent state across queries
- Transactions for complex updates
- Durable storage

### Migration Path: Redis → Neo4j

**Option A: Dual Mode (Gradual Migration)**
```python
class HybridGraphBackend:
    def __init__(self):
        self.redis = RedisCacheBackend()  # Fast cache
        self.neo4j = Neo4jDriver()        # Advanced queries
        self.rustworkx_graph = UniversalGraph()  # In-memory
    
    async def add_node(self, node):
        # Write to all three
        self.rustworkx_graph.add_node(node)
        await self.redis.set_file_nodes(...)  # Cache
        await self.neo4j.create_node(node)    # Persistent graph
    
    async def find_all_paths(self, start, end):
        # Use Neo4j for complex queries
        return await self.neo4j.query("""
            MATCH path = (start:Function {id: $start})
                        -[:CALLS*1..20]->
                        (end:Function {id: $end})
            RETURN path
        """, start=start, end=end)
```

**Option B: ETL Pipeline (Redis → Neo4j sync)**
```python
async def sync_graph_to_neo4j():
    """One-way sync: rustworkx/Redis → Neo4j"""
    # Read from Redis cache
    all_nodes = await redis.get_all_cached_nodes()
    all_rels = await redis.get_all_cached_relationships()
    
    # Batch write to Neo4j
    async with neo4j.session() as session:
        # Create nodes
        await session.run("""
            UNWIND $nodes as node
            MERGE (n:Function {id: node.id})
            SET n.name = node.name,
                n.complexity = node.complexity,
                n.language = node.language
        """, nodes=all_nodes)
        
        # Create relationships
        await session.run("""
            UNWIND $rels as rel
            MATCH (a {id: rel.source_id})
            MATCH (b {id: rel.target_id})
            MERGE (a)-[r:CALLS]->(b)
        """, rels=all_rels)
```

**Option C: Neo4j Only (Full Migration)**
- Replace rustworkx entirely
- Use Neo4j as primary graph storage
- Keep Redis only for HTTP response caching
- Simpler architecture, but requires Neo4j infrastructure

### Neo4j Pros/Cons

**Pros**:
- Cypher is incredibly powerful for complex queries
- Built-in algorithms (shortest path, centrality, community detection)
- ACID compliance for data integrity
- Scales to billions of nodes/edges
- Neo4j Bloom for graph visualization
- Active community and excellent documentation

**Cons**:
- Additional infrastructure (another Docker container)
- Learning curve for Cypher
- Heavier resource usage than Redis
- Requires ETL pipeline or dual-write logic
- Licensing: Community Edition (GPLv3) vs Enterprise ($$$)

---

## Memgraph: Event-Driven Graph Database

### Why Memgraph Over Neo4j?
1. **Performance**: 10-100x faster for real-time queries (in-memory first)
2. **Event-Driven Native**: Built-in Kafka/Redis Streams support
3. **Cypher Compatible**: Standard query language, easy learning curve
4. **Lower Latency**: <1ms for simple queries vs Neo4j's 10-50ms  
5. **Smaller Footprint**: ~500MB RAM vs Neo4j's 2GB+
6. **Licensing**: Free for <4 cores (dev-friendly)

### Event-Driven Integration with Redis Streams
**Why This Matters for Code Graphs**:
- Code changes trigger analysis → CDC events → Memgraph auto-updates
- File watcher detects changes → incremental re-parse → stream delta to Memgraph
- LLM generates summaries → stored in Redis JSON → linked to graph nodes
- Real-time collaboration: Multiple users see live graph updates via Pub/Sub

### Memgraph Use Cases for Code Graph
```cypher
// Real-time: Find impacted functions when file changes
MATCH (changed:Function {file: $changed_file})
MATCH (impacted:Function)-[:CALLS*1..5]->(changed)
RETURN impacted

// Streaming: Process code changes as events
CREATE STREAM code_changes
ON MESSAGE AS msg
CALL analyze_impact(msg.file_path)

// Graph ML: Train model on call patterns
CALL pagerank.get() YIELD node, rank
WHERE node.language = 'Python'
RETURN node.name, rank
ORDER BY rank DESC
LIMIT 10
```

**Decision**: Memgraph chosen as primary graph database for event-driven architecture.

### Docker Compose Integration
```yaml
services:
  memgraph:
    image: memgraph/memgraph-platform:latest
    ports:
      - "7687:7687"  # Bolt protocol (Cypher queries)
      - "3000:3000"  # Memgraph Lab UI
    environment:
      - MEMGRAPH_LOG_LEVEL=WARNING
    volumes:
      - memgraph-data:/var/lib/memgraph
    command: ["--stream-enabled=true"]
  
  memgraph-sync-worker:
    build:
      context: .
      dockerfile: Dockerfile
      target: sync-worker
    depends_on:
      - redis
      - memgraph
    environment:
      - REDIS_URL=redis://redis:6379
      - MEMGRAPH_URL=bolt://memgraph:7687
```

---

## Redis ↔ Graph Database Connectors

### Redis Streams → Memgraph CDC Pipeline

**Pattern 1: Event-Driven Sync (Recommended)**
```python
# Use Redis Streams as CDC log
async def on_graph_mutation(event):
    # Write to Redis Stream
    await redis.xadd('graph:cdc', {
        'type': event.type,  # 'node_added', 'edge_added'
        'data': json.dumps(event.data)
    })

# Separate worker consumes stream and syncs to Neo4j
async def memgraph_sync_worker():
    """Background worker consuming Redis Streams and syncing to Memgraph."""
    last_id = '0-0'  # Start from beginning
    
    while True:
        # Block for 1 second waiting for new events
        messages = await redis.xread({'graph:cdc': last_id}, block=1000)
        
        for stream_id, msg in messages:
            event_type = msg['type']
            data = json.loads(msg['data'])
            
            if event_type == 'node_added':
                await memgraph.execute("""
                    MERGE (n:Node {id: $id})
                    SET n.name = $name,
                        n.node_type = $node_type,
                        n.language = $language
                """, data)
            
            elif event_type == 'edge_added':
                await memgraph.execute("""
                    MATCH (a {id: $source_id})
                    MATCH (b {id: $target_id})
                    MERGE (a)-[r:CALLS]->(b)
                    SET r.type = $rel_type
                """, data)
            
            last_id = stream_id  # Update cursor
```

**Pattern 2: Dual Write (Not Recommended - Breaks Event Sourcing)**
```python
# DON'T DO THIS - Loses CDC audit trail
async def add_relationship(rel):
    await asyncio.gather(
        redis.set_relationship(rel),
        memgraph.create_relationship(rel)  # Bypasses event log
    )
```

**Why Event-Driven is Better**:
- Single source of truth (Redis Streams)
- Replay events for debugging
- Easy to add more consumers (analytics, exports)
- Decouples write path from read path

**Pattern 3: Query Router (Recommended)**
```python
class HybridGraphQueryEngine:
    """Route queries to rustworkx (fast) or Memgraph (complex)."""
    
    async def find_callers(self, symbol: str):
        # Simple query → Use rustworkx (in-memory, <1ms)
        return self.rustworkx_graph.predecessors(symbol)
    
    async def find_all_paths(self, start: str, end: str, max_hops: int = 10):
        # Complex query → Use Memgraph Cypher
        return await self.memgraph.query("""
            MATCH path = (a:Function {id: $start})
                        -[:CALLS*1..$max_hops]->
                        (b:Function {id: $end})
            RETURN path
            ORDER BY length(path)
            LIMIT 10
        """, start=start, end=end, max_hops=max_hops)
    
    async def find_architectural_seams(self):
        # Pattern matching → Only Cypher can do this efficiently
        return await self.memgraph.query("""
            MATCH (a:Function)-[r:CALLS]->(b:Function)
            WHERE a.file <> b.file
            WITH a.file as file_a, b.file as file_b, count(r) as coupling
            WHERE coupling > 10
            RETURN file_a, file_b, coupling
            ORDER BY coupling DESC
        """)
```

### Memgraph Stream Support
**Built-in Streaming**: Memgraph has native Redis Streams support via transformations.

```cypher
-- Create Memgraph stream transformation
CREATE STREAM code_graph_events
TOPICS graph:cdc
TRANSFORM memgraph_stream.parse_json
BATCH_SIZE 100;

-- Process events with Cypher
CREATE TRIGGER on_node_added
ON CREATE BEFORE COMMIT
EXECUTE
MATCH (n:TempNode)
MERGE (m:Function {id: n.id})
SET m = properties(n);
```

**Benefits**:
- No separate sync worker needed (Memgraph reads Redis directly)
- Lower latency (near real-time sync)
- Simpler architecture

---

## Redis GraphQL Support

### RedisGraph (Deprecated)
- Had GraphQL-like Cypher support
- End-of-life November 2023
- Recommended migration: Neo4j, Memgraph, or ArangoDB

### Current Options for GraphQL over Redis

**Option 1: GraphQL Server Layer**
```python
import strawberry
from strawberry.asgi import GraphQL

@strawberry.type
class Function:
    id: str
    name: str
    complexity: int
    callers: list['Function']  # Resolver fetches from Redis

@strawberry.type
class Query:
    @strawberry.field
    async def function(self, name: str) -> Function:
        # Query Redis cache
        data = await redis.get(f'function:{name}')
        return Function(**data)
    
    @strawberry.field
    async def call_chain(self, start: str, end: str) -> list[Function]:
        # Run rustworkx algorithm, cache result
        ...

schema = strawberry.Schema(query=Query)
graphql_app = GraphQL(schema)
```

**Option 2: Hasura + Redis**
- Hasura can't directly connect to Redis
- Would need PostgreSQL with RedisGraph data synced
- Overly complex for our use case

**Recommendation**: GraphQL over FastAPI + Redis is doable but adds complexity without clear benefit over REST API.

---

## Comparison Matrix

| Feature | Current (Rustworkx + Redis) | Neo4j | Memgraph | ArangoDB |
|---------|----------------------------|-------|----------|----------|
| **Query Language** | Python methods | Cypher | Cypher | AQL |
| **Performance** | Fast (in-memory Rust) | Medium | Very Fast | Medium-Fast |
| **Scalability** | <100K nodes | Billions | Millions | Billions |
| **Built-in Algorithms** | Rustworkx only | 70+ algorithms | 30+ algorithms | Graph algorithms |
| **ACID** | ❌ (in-memory) | ✅ Full | ✅ Full | ✅ Full |
| **Infrastructure** | Redis only | +Neo4j container | +Memgraph container | +ArangoDB container |
| **Learning Curve** | Low | Medium (Cypher) | Medium (Cypher) | High (AQL) |
| **Cost** | Free | Community free / Enterprise $$$ | Free <4 cores | Community free |
| **Graph ML** | ❌ | Neo4j GDS ($$$) | ✅ Built-in | Limited |
| **Streaming** | Redis Streams | ❌ | ✅ Kafka/Pulsar | ✅ |
| **License** | MIT | GPLv3 / Commercial | Business Source | Apache 2.0 |

---

## Recommended Architecture: Memgraph + Event-Driven Pipeline

### Phase 1 (Session 13-14): Redis Enhancements + CDC Foundation
**Enhance Redis with streaming capabilities**:

1. **Redis Streams** for Change Data Capture (CDC)
   - Every graph mutation published as event (node_added, edge_added, etc)
   - Event log enables replay, undo, and downstream sync
2. **Redis Pub/Sub** for real-time notifications
   - Analysis completion, progress updates, LLM summaries
3. **Redis JSON** for storing analysis metadata
4. **Redis Search** for full-text node search

**Benefits**:
- Event-driven foundation for Memgraph sync
- No new infrastructure yet (stay fast)
- Real-time frontend updates via WebSocket

### Phase 2 (Session 15-16): Memgraph Integration
**Add Memgraph as queryable graph database**:

```
Parse Code → Rustworkx (in-memory, fast) → Redis Streams (CDC log)
                                                  ↓
                                            Memgraph Sync Worker
                                                  ↓
                                            Memgraph (Cypher queries)
```

**Event-Driven Sync Pipeline**:
```python
# Publisher: Emit CDC events on every graph mutation
async def add_node_to_graph(node):
    rustworkx_graph.add_node(node)
    await redis.set_file_nodes(...)  # Cache
    
    # Publish CDC event
    await redis.xadd('graph:cdc', {
        'event': 'node_added',
        'node_id': node.id,
        'data': json.dumps(asdict(node))
    })

# Consumer: Background worker syncs to Memgraph
async def memgraph_sync_worker():
    while True:
        messages = await redis.xread({'graph:cdc': last_id}, block=1000)
        for msg in messages:
            if msg['event'] == 'node_added':
                await memgraph.create_node(msg['data'])
            elif msg['event'] == 'edge_added':
                await memgraph.create_relationship(msg['data'])

# Simple queries use rustworkx (fast)
async def find_callers(symbol):
    return rustworkx_graph.find_callers(symbol)  # <1ms

# Complex queries use Memgraph Cypher (powerful)
async def find_business_logic_paths():
    return await memgraph.query("""
        MATCH path = (http:Function {type: 'endpoint'})
                    -[:CALLS*1..10]->
                    (db:Function)
        WHERE db.file CONTAINS 'repository' 
           OR db.file CONTAINS 'dao'
        RETURN path
    """)
```

**Benefits**:
- Best of both worlds (fast parsing, powerful queries)
- Rustworkx for real-time analysis
- Neo4j for knowledge mining
- Can deprecate Neo4j if not needed (no vendor lock-in)

### Phase 3 (Future): MCP Prompts & Resources Library
**Add MCP resources for common code navigation patterns**:
```python
# MCP Resources - Pre-built Cypher queries
resources = [
    {
        "uri": "cypher://find-entry-to-db-paths",
        "name": "Find Entry Point → DB Paths",
        "query": """
            MATCH path = (entry:Function {is_entry_point: true})
                        -[:CALLS*1..15]->
                        (db:Function)
            WHERE db.name =~ '.*(insert|update|delete|save).*'
            RETURN path
        """
    },
    {
        "uri": "cypher://impact-analysis",
        "name": "Impact Analysis for Function",
        "query": """
            MATCH (changed:Function {name: $symbol})
            MATCH (impacted)-[:CALLS*1..10]->(changed)
            RETURN impacted.name, length(path) as distance
        """
    }
]
```

**MCP Prompts** - Common developer workflows:
- "Show me authentication flow" → Entry point → auth boundary → session management
- "What breaks if I change X?" → Impact analysis with test coverage
- "Find architectural seams" → High coupling between modules

---

## Specific Use Cases: Why Graph DB?

### 1. **Find Hidden Business Logic**
**Query**: "Show me all code paths from HTTP endpoint to database write"

```cypher
// Neo4j/Memgraph Cypher
MATCH path = (http:Function {decorator: '@app.post'})
            -[:CALLS*1..15]->
            (db:Function)
WHERE db.name =~ '.*(insert|update|delete|save).*'
  AND (db)-[:CALLS]->(:Function {name: 'execute'})
RETURN path, length(path) as hops
ORDER BY hops
```

**Rustworkx equivalent**: Would need custom BFS with predicate matching. Doable but verbose.

### 2. **Impact Analysis**
**Query**: "If I change function X, what breaks?"

```cypher
MATCH (changed:Function {name: 'authenticate_user'})
MATCH (impacted:Function)-[:CALLS*1..10]->(changed)
OPTIONAL MATCH (impacted)-[:CALLS]->(test:Function)
WHERE test.file CONTAINS 'test'
RETURN impacted.name, 
       count(test) as test_coverage,
       length(path) as distance
ORDER BY distance
```

### 3. **Architectural Queries**
**Query**: "Find all microservice boundaries (cross-file high coupling)"

```cypher
MATCH (a:Function)-[r:CALLS]->(b:Function)
WHERE a.file <> b.file
WITH a.file as file_a, b.file as file_b, count(r) as coupling
WHERE coupling > 10
RETURN file_a, file_b, coupling
ORDER BY coupling DESC
```

### 4. **Code Quality Patterns**
**Query**: "Find functions with high complexity and many callers (refactoring targets)"

```cypher
MATCH (func:Function)<-[:CALLS]-(caller)
WHERE func.complexity > 15
WITH func, count(caller) as caller_count
WHERE caller_count > 10
RETURN func.name, func.complexity, caller_count
ORDER BY func.complexity * caller_count DESC
LIMIT 20
```

**All of these are possible with rustworkx**, but require writing custom Python functions. With Neo4j/Memgraph, they're one-line Cypher queries.

---

## Redis GraphQL: Not Worth It

**Conclusion**: Redis doesn't natively support GraphQL.

**Options**:
1. Build GraphQL server on top of FastAPI + Redis (adds complexity)
2. Use REST API with good design (current approach - works well)

**Recommendation**: Stick with REST API. GraphQL doesn't add significant value for our use case (mostly simple queries, not deeply nested).

---

## What Redis CAN Do Beyond Caching

### Recommended Enhancements (Session 14+)

**1. Redis Streams for Live Updates**
```python
# Backend publishes events
await redis.xadd('graph:events', {
    'type': 'analysis_progress',
    'files_processed': 45,
    'total_files': 78
})

# Frontend subscribes via SSE
@app.get('/events')
async def event_stream():
    async for event in redis.xread('graph:events'):
        yield f"data: {json.dumps(event)}\n\n"
```

**2. Redis Pub/Sub for Notifications**
```python
# Analysis completion
await redis.publish('analysis:complete', json.dumps({
    'nodes': 489,
    'relationships': 4475
}))
```

**3. Redis Search for Better Node Search**
```python
# Create searchable index
await redis.ft('nodes').create_index([
    TextField('name', weight=2.0),
    TextField('docstring'),
    TagField('language'),
    NumericField('complexity')
])

# Full-text search with ranking
results = await redis.ft('nodes').search(
    'authentication @language:{Python}',
    sortby='complexity DESC'
)
```

**4. Redis JSON for Metadata**
```python
# Store LLM-generated summaries
await redis.json().set(f'summary:{node_id}', Path.root_path(), {
    'summary': 'This function handles user authentication...',
    'generated_at': datetime.now().isoformat(),
    'model': 'claude-3-sonnet',
    'tags': ['security', 'auth']
})
```

---

## Final Architecture Decision

### Phase 1: Redis Enhancements (Session 13-14) ✅
**Implement event-driven foundation**:
1. ✅ Redis Streams for CDC (every graph mutation logged)
2. ✅ Redis Pub/Sub for real-time notifications
3. ✅ Redis Search for full-text node search
4. ✅ Redis JSON for analysis metadata

**Deliverables**:
- CDC event publisher in UniversalParser
- WebSocket endpoint for live frontend updates
- Search API endpoint with Redis Search

### Phase 2: Memgraph Integration (Session 15-16) 🎯
**Add Memgraph with event-driven sync**:
1. 🎯 Memgraph container in docker-compose
2. 🎯 Stream transformation or sync worker consuming Redis Streams
3. 🎯 Dual query strategy (simple → rustworkx, complex → Cypher)
4. 🎯 MCP Resources library with pre-built Cypher queries

**Deliverables**:
- Memgraph sync worker or native stream transformation
- GraphQueryRouter class (routes queries to optimal backend)
- 10+ MCP Resources for common navigation patterns
- Playwright tests for complex query features

### Phase 3: MCP Prompts & Workflow Patterns (Session 17+) 🔮
**Codebases-as-knowledge-graphs UX**:
1. 🔮 MCP Prompts library ("Show auth flow", "Impact analysis", etc)
2. 🔮 Natural language → Cypher query generation (LLM-assisted)
3. 🔮 Visual query builder in frontend
4. 🔮 Saved queries and bookmarks

**Why This Architecture**:
- ✅ Event-driven enables real-time updates and replay
- ✅ Memgraph provides Cypher power with low latency
- ✅ Hybrid approach keeps parsing fast (rustworkx)
- ✅ MCP integration makes complex queries accessible
- ✅ Can still migrate to Neo4j later (Cypher compatible)

---

## Infrastructure Cost Comparison

### Current Stack
- Redis: ~50MB RAM
- Backend: ~200MB RAM
- Total: ~250MB + CPU for analysis

### With Neo4j
- Redis: ~50MB
- Backend: ~200MB  
- Neo4j: ~2GB minimum (4GB recommended)
- Total: ~4.5GB

### With Memgraph
- Redis: ~50MB
- Backend: ~200MB
- Memgraph: ~500MB
- Total: ~750MB

**For Local Development**: Memgraph is more practical.  
**For Production**: Neo4j has better tooling and community support.

---

**Next Steps**: 
1. Session 13 P0 fixes (pagination, layout, stdlib filtering)
2. Session 13 P1: Implement Redis Streams CDC
3. Session 14: Add Redis Pub/Sub + Search
4. Session 15: Integrate Memgraph with event-driven sync
5. Session 16: Build MCP Resources library for Cypher patterns

**Testing Strategy**: Continue Playwright-first development for all UI features.
