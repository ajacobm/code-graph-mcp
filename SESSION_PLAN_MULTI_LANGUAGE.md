# Multi-Language Graph Visualization & Query System - Session Plan

## Overview
Build a complete REST API + Vue.js UI for visualizing and querying code graphs across multiple languages with cross-language seam tracking.

**Duration**: 2-3 sessions  
**Tech Stack**: FastAPI (REST), Vue 3, rustworkx graphs, DuckDB (for future optimization)  
**Starting Branch**: `feature/cross-language-seams` (has IgnorePatternsManager + SeamDetector)

---

## Session 1: REST API Layer & Graph Traversal Queries

### Goals
1. Extend FastAPI server with graph query endpoints
2. Implement traversal algorithms (depth-first, breadth-first call chains)
3. Add SEAM-aware path finding for cross-language calls
4. Cache query results for performance

### Tasks

#### 1.1 Graph Query API Endpoints
Create new file: `src/code_graph_mcp/server/graph_api.py`

Implement endpoints:
```python
# Core traversal
GET /api/graph/nodes/{node_id}
GET /api/graph/relationships
GET /api/graph/traverse
  - query_type: "dfs" | "bfs" | "call_chain"
  - start_node: str
  - max_depth: int
  - include_seams: bool (follow SEAM edges)

# Filtering & search
GET /api/graph/nodes/search?name=...&language=...&type=...
GET /api/graph/stats (node count, relationship types, languages)

# Seam-specific
GET /api/graph/seams (all cross-language edges)
GET /api/graph/seams/from/{node_id} (seams originating from node)
GET /api/graph/call-chain/{start_node}?follow_seams=true
  - Returns complete call chain including cross-language boundaries
```

**Files to modify**:
- `src/code_graph_mcp/server/mcp_server.py` - integrate traversal functions
- `src/code_graph_mcp/graph/traversal.py` - add SEAM-aware algorithms

**Tests**:
- `tests/test_graph_api.py` - endpoint tests
- `tests/test_seam_traversal.py` - cross-language path finding

#### 1.2 Traversal Algorithm Enhancements
Extend `src/code_graph_mcp/graph/traversal.py`:

```python
def dfs_traversal(
    graph: RustworkxGraphCore,
    start_node_id: str,
    max_depth: int = 10,
    include_seams: bool = True,
    visited: Set[str] = None
) -> Dict[str, Any]:
    """DFS with SEAM edge tracking"""

def find_call_chain(
    graph: RustworkxGraphCore,
    start_node_id: str,
    end_node_id: str,
    follow_seams: bool = True
) -> List[Tuple[str, str]]:
    """Find shortest path between nodes, optionally crossing language boundaries"""

def trace_cross_language_flow(
    graph: RustworkxGraphCore,
    start_node_id: str
) -> Dict[str, List[Dict]]:
    """Trace execution flow across language boundaries (C# -> Node -> SQL)"""
```

**Tests**:
- Path finding with/without seams
- Complex multi-tier scenarios (3+ languages)
- Performance: 1000-node graph traversal should be <100ms

#### 1.3 Query Result Serialization
Create: `src/code_graph_mcp/graph/query_response.py`

```python
@dataclass
class NodeResponse:
    id: str
    name: str
    type: str
    language: str
    location: Dict[str, Any]
    metadata: Dict[str, Any]

@dataclass
class RelationshipResponse:
    id: str
    source: NodeResponse
    target: NodeResponse
    type: str
    is_seam: bool
    metadata: Dict[str, Any]

@dataclass
class TraversalResponse:
    nodes: List[NodeResponse]
    edges: List[RelationshipResponse]
    stats: Dict[str, int]
    execution_time_ms: float
```

### Deliverables
- [ ] `/api/graph/*` endpoints working
- [ ] Traversal tests pass (22+ test cases)
- [ ] Call chain tracing with seam awareness
- [ ] Response serialization benchmarked

### Branch
Create: `feature/graph-query-api` from `feature/cross-language-seams`

---

## Session 2: Vue.js UI & Graph Visualization

### Goals
1. Build Vue 3 component architecture for graph visualization
2. Integrate vis.js or Cytoscape.js for interactive rendering
3. Implement filtering, search, and drill-down navigation
4. Real-time updates (WebSocket or polling)

### Tech Choices
- **Framework**: Vue 3 (Composition API)
- **Visualization**: Cytoscape.js (better for DAGs, call graphs)
  - Alternative: vis.js (simpler, better force-directed layout)
- **HTTP**: axios + vue-query for caching
- **Build**: Vite
- **Styling**: Tailwind CSS or shadcn/vue

**Decision**: Start with Cytoscape.js for call graph, consider vis.js if performance issues.

### Tasks

#### 2.1 Project Structure
```
frontend/
├── src/
│   ├── components/
│   │   ├── GraphViewer.vue (main visualization)
│   │   ├── NodeDetails.vue (right panel - node info)
│   │   ├── SearchBar.vue (find nodes/calls)
│   │   ├── FilterPanel.vue (language, type filters)
│   │   └── CallChainTracer.vue (step through calls)
│   ├── stores/ (Pinia)
│   │   ├── graphStore.ts (graph data, API state)
│   │   └── filterStore.ts (active filters)
│   ├── api/
│   │   └── graphClient.ts (axios wrapper)
│   └── App.vue
├── package.json
└── vite.config.ts
```

#### 2.2 Core Components

**GraphViewer.vue**:
- Loads graph data from `/api/graph/traverse`
- Renders nodes + edges with Cytoscape
- Highlights SEAM edges (dashed, different color)
- Click node → shows details + incoming/outgoing calls
- Hover → tooltip with node metadata

**NodeDetails.vue**:
- Shows full node info (location, complexity, docstring, etc)
- Lists incoming calls (find_callers)
- Lists outgoing calls (find_callees)
- Button to "Trace to entry point"

**CallChainTracer.vue**:
- Step-by-step navigation: Entry → ... → End
- Each step expandable to show SEAM crossings
- Visual highlight of active path
- Export to JSON/CSV

**FilterPanel.vue**:
- Filter by language(s) - multi-select
- Filter by node type (function, class, etc)
- Limit to SEAM relationships only
- Min/max complexity slider

#### 2.3 API Integration
Create `src/api/graphClient.ts`:

```typescript
import axios from 'axios'

const API_BASE = 'http://localhost:8000/api'

export interface TraversalQuery {
  startNode: string
  queryType: 'dfs' | 'bfs' | 'call_chain'
  maxDepth: number
  includeSeams: boolean
  filters?: {
    languages?: string[]
    nodeTypes?: string[]
  }
}

export class GraphClient {
  async traverse(query: TraversalQuery) { }
  async searchNodes(name: string) { }
  async getNodeDetails(nodeId: string) { }
  async getCallChain(from: string, to: string, followSeams: boolean) { }
  async getStats() { }
}
```

#### 2.4 State Management (Pinia)
```typescript
// stores/graphStore.ts
interface GraphState {
  nodes: Map<string, Node>
  edges: Map<string, Edge>
  selectedNodeId: string | null
  isLoading: boolean
  viewMode: 'full' | 'call_chain' | 'seams_only'
}

// Actions
- loadGraph(query: TraversalQuery)
- selectNode(nodeId: string)
- filterByLanguage(languages: string[])
- traceCallChain(from: string, to: string)
```

### Deliverables
- [ ] Vue 3 + Vite project setup
- [ ] GraphViewer renders 100+ node graphs smoothly
- [ ] SEAM edges visually distinct
- [ ] Node click → details panel
- [ ] Filter panel works (language, type)
- [ ] Call chain tracer step-through
- [ ] Responsive design (1366+ width)

### Branch
Create: `feature/graph-ui-vue` from `feature/graph-query-api`

---

## Session 3: Advanced Features & Optimization

### Goals
1. DuckDB integration for complex graph queries
2. Performance optimization (1M+ node graphs)
3. Advanced features: tagging, annotations, comparison
4. Deployment & documentation

### Tasks

#### 3.1 DuckDB Integration
Create: `src/code_graph_mcp/graph/parquet_export.py`

```python
def export_to_parquet(graph: RustworkxGraphCore, output_path: str):
    """Export graph to Parquet format for DuckDB analysis"""
    # Nodes table: id, name, type, language, complexity, location
    # Edges table: source_id, target_id, relationship_type, is_seam

def import_from_duckdb(query: str) -> RustworkxGraphCore:
    """Load graph subset from DuckDB SQL query"""
    # Example: SELECT * FROM edges WHERE source_language='csharp' AND target_language='node'
```

**Enables**:
```sql
-- Find all C# functions calling Node services
SELECT e.source_id, e.target_id, n1.name, n2.name
FROM edges e
JOIN nodes n1 ON e.source_id = n1.id
JOIN nodes n2 ON e.target_id = n2.id
WHERE e.is_seam = true AND n1.language = 'csharp' AND n2.language = 'node'

-- Find most complex call chains
SELECT COUNT(*) as call_depth, source_id
FROM edges
WHERE relationship_type = 'calls'
GROUP BY source_id
ORDER BY call_depth DESC
LIMIT 20
```

#### 3.2 Graph Tagging & Annotations
Create: `src/code_graph_mcp/graph/tagging.py`

```python
@dataclass
class Tag:
    id: str
    label: str
    color: str
    description: str

class TagManager:
    def tag_node(self, node_id: str, tag_id: str) -> None: ...
    def tag_relationship(self, rel_id: str, tag_id: str) -> None: ...
    def find_by_tag(self, tag_id: str) -> Set[str]: ...
    def export_tagged_graph(self, tag_id: str) -> Dict: ...
```

**Use cases**:
- Tag deprecated functions
- Mark security-critical seams (untrusted code boundaries)
- Highlight performance bottlenecks
- Annotate "legacy" vs "new" code

#### 3.3 Graph Comparison
Create: `src/code_graph_mcp/graph/diff.py`

```python
def compare_graphs(old: RustworkxGraphCore, new: RustworkxGraphCore) -> GraphDiff:
    """Find added/removed/modified nodes and relationships"""
    # Returns: added_nodes, removed_nodes, changed_relationships, orphaned_nodes
```

**UI**: Show before/after graphs side-by-side.

#### 3.4 Performance Optimization
- Lazy-load large graphs (load viewport first, stream rest)
- Implement pagination for node lists (50/page)
- Cache traversal results in Redis
- Profile UI with Chrome DevTools (target: 60 FPS)

#### 3.5 Docker & Deployment
Create:
- `docker-compose-ui.yml` - API + UI + Redis
- `frontend/.dockerignore`
- Nginx config for static Vue build + reverse proxy

### Deliverables
- [ ] DuckDB export/import working
- [ ] Tag system fully functional
- [ ] Graph diff showing changes
- [ ] UI renders 10,000+ nodes without lag
- [ ] Docker compose runs full stack
- [ ] README with deployment instructions

### Branch
Create: `feature/graph-duckdb-advanced` from `feature/graph-ui-vue`

---

## Architecture Diagram

```
Code Repository
    ↓
UniversalParser + SeamDetector
    ↓
RustworkxGraph (with SEAM edges)
    ↓
FastAPI Server ← ← ← REST API ← ← ← Vue3 UI (Cytoscape.js)
    ↓
Redis Cache (traversal results)
    ↓
DuckDB/Parquet (advanced queries)
```

---

## Testing Strategy

### Unit Tests (by session)
- **Session 1**: 25+ tests for traversal algorithms, SEAM paths
- **Session 2**: 15+ component tests (Vue), snapshot tests
- **Session 3**: 10+ tests for DuckDB/tagging

### Integration Tests
- Full graph load → query → visualize pipeline
- Cross-language call tracing end-to-end
- Multi-tier architecture (3+ languages)

### Performance Tests
- Graph with 10K nodes: traversal <200ms
- Vue renders 500+ nodes: 60 FPS
- DuckDB query on Parquet: <1s for 1M rows

---

## Known Unknowns / Decisions Needed

1. **Visualization Library**: Cytoscape.js vs vis.js
   - Cytoscape: DAG layout, better for call graphs
   - vis.js: Force-directed, good for general graphs
   - **Recommendation**: Start Cytoscape, switch if needed

2. **Real-Time Updates**: WebSocket vs Polling
   - For now: Polling with 5s interval
   - Later: WebSocket if multiple users need live updates

3. **Authentication**: Not in scope for MVP
   - Assume single-user or trusted network

4. **Large Graph Handling**: When graph > 100K nodes
   - Use viewport-based loading (Cytoscape.js handles this)
   - DuckDB can filter before visualization

---

## Success Criteria
- [ ] Visualize multi-tier .NET + Node + SQL codebase
- [ ] Trace call chain through all 3 languages
- [ ] SEAM relationships visually obvious
- [ ] Filter by language reduces graph intelligently
- [ ] Call chain tracer shows execution flow across runtimes
- [ ] UI responsive on modern browsers
- [ ] API + UI deployable via docker-compose

---

## Resources
- Cytoscape.js docs: https://js.cytoscape.org/
- vis.js docs: https://visjs.org/
- Vue 3 composition API: https://vuejs.org/guide/extras/composition-api-faq.html
- DuckDB docs: https://duckdb.org/docs/
- FastAPI + Pydantic: https://fastapi.tiangolo.com/

---

## Rollback Plan
If a session encounters blockers:
1. Revert to previous feature branch
2. Commit findings in `BLOCKER_NOTES.md`
3. Adjust plan + create alternative approach branch
