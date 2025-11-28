# Force-Directed Graph Visualization UI Plan

**Version**: 1.0  
**Date**: November 2025  
**Status**: Planning Phase

---

## Executive Summary

This document outlines the technical plan for building a new force-directed graph visualization UI for CodeNavigator. The UI will serve as a **logic graph and business use case logic finder and traversal workbench**, replacing the existing Vue-based frontend with a purpose-built graph visualization interface.

---

## 1. Existing HTTP API Evaluation

### 1.1 API Endpoints Available for Reuse

The existing FastAPI backend (`src/codenav/http_server.py`, `src/codenav/server/graph_api.py`) provides a comprehensive REST API that is **fully reusable**:

| Endpoint | Method | Description | Reuse Status |
|----------|--------|-------------|--------------|
| `/api/graph/stats` | GET | Graph statistics (nodes, relationships, languages) | ✅ Reuse |
| `/api/graph/nodes/{node_id}` | GET | Get single node details | ✅ Reuse |
| `/api/graph/nodes/search` | GET | Search nodes by name/language/type | ✅ Reuse |
| `/api/graph/traverse` | POST | BFS/DFS traversal from node | ✅ Reuse |
| `/api/graph/call-chain/{node}` | GET | Call chain analysis | ✅ Reuse |
| `/api/graph/categories/{cat}` | GET | Get entry points, hubs, leaves | ✅ Reuse |
| `/api/graph/seams` | GET | Cross-language relationships | ✅ Reuse |
| `/api/graph/subgraph` | POST | Focused subgraph around a node | ✅ Reuse |
| `/api/graph/query/callers` | GET | Find function callers | ✅ Reuse |
| `/api/graph/query/callees` | GET | Find function callees | ✅ Reuse |
| `/api/graph/query/references` | GET | Find symbol references | ✅ Reuse |
| `/api/graph/entry-points` | GET | Detected entry points | ✅ Reuse |
| `/api/graph/admin/reanalyze` | POST | Force re-analysis | ✅ Reuse |

### 1.2 WebSocket Server for Real-Time Events

The existing WebSocket server (`src/codenav/websocket_server.py`) provides:

- **`/ws/events`** - Real-time CDC event streaming
- **`/ws/events/filtered`** - Filtered event subscription
- **`/ws/status`** - Connection status

This is **perfect for MCP session observation hooks** - clients can subscribe to graph traversal events in real-time.

### 1.3 API Enhancements Needed

| Enhancement | Priority | Description |
|-------------|----------|-------------|
| Full graph export | High | New endpoint: `/api/graph/export` - Returns all nodes/edges for force-graph |
| Cluster detection | Medium | New endpoint: `/api/graph/clusters` - Module/namespace clustering |
| Path finding | Medium | New endpoint: `/api/graph/path/{from}/{to}` - Shortest path between nodes |
| Node annotations | Medium | CRUD endpoints for node annotations/metadata |
| Graph filtering | Low | Server-side filter: `/api/graph/filter` with complex queries |

---

## 2. Force-Directed Graph Library Evaluation

### 2.1 Library Comparison

| Library | License | Performance | WebGL | 3D | Customization | Maturity | Bundle Size |
|---------|---------|-------------|-------|-----|---------------|----------|-------------|
| **force-graph** | MIT | ⭐⭐⭐⭐⭐ | Canvas/WebGL | ✅ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ~100KB |
| **D3-force** | ISC | ⭐⭐⭐⭐ | SVG only | ❌ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ~30KB |
| **Sigma.js** | MIT | ⭐⭐⭐⭐⭐ | WebGL | ❌ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ~150KB |
| **Cytoscape.js** | MIT | ⭐⭐⭐ | Canvas | ❌ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ~400KB |
| **vis-network** | MIT | ⭐⭐⭐ | Canvas | ❌ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ~300KB |
| **3d-force-graph** | MIT | ⭐⭐⭐⭐ | WebGL | ✅ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ~200KB |

### 2.2 Recommendation: **force-graph** (already in package.json!)

**Reasons:**
1. **Already installed** - `"force-graph": "^1.51.0"` in `frontend/package.json`
2. **Performance** - Handles 10,000+ nodes with WebGL acceleration
3. **Flexibility** - Canvas/WebGL/SVG rendering options
4. **3D Support** - `3d-force-graph` is a companion library for 3D visualization
5. **Active Maintenance** - Regular updates, good documentation
6. **MIT License** - No licensing concerns
7. **Real-time Updates** - Designed for dynamic graph updates

**Alternative for Hybrid Approach:**
- Use `force-graph` for main visualization
- Use `Cytoscape.js` (already installed) for advanced analysis algorithms

---

## 3. Tech Stack Decision

### 3.1 Framework Comparison

| Framework | Pros | Cons | Desktop | Web | Recommendation |
|-----------|------|------|---------|-----|----------------|
| **Electron + React** | Native feel, filesystem access, single codebase | Bundle size (~150MB), memory overhead | ✅ | ✅ (web builds) | ⭐ **Top Choice** |
| **React (SPA)** | Lightweight, fast development, wide ecosystem | No native features | ❌ | ✅ | Good for web-only |
| **Vue 3** (current) | Already setup, reactive state | Less graph ecosystem than React | ❌ | ✅ | Continue if keeping Vue |
| **AvaloniaUI** | C#/.NET, cross-platform, lightweight | Smaller ecosystem, .NET dependency | ✅ | ❌ (WASM) | For .NET-centric projects |
| **Tauri + React** | Tiny bundles (~10MB), Rust backend | Less mature than Electron | ✅ | ✅ | ⭐ **Modern Alternative** |

### 3.2 Recommended Stack: **React + Tauri** (with Electron fallback)

**Primary Stack:**
```
├── Frontend Framework: React 18 with TypeScript
├── State Management: Zustand or Jotai (simpler than Redux)
├── Graph Visualization: force-graph + 3d-force-graph
├── UI Components: Radix UI + Tailwind CSS
├── Desktop Wrapper: Tauri (Rust-based, ~10MB bundle)
├── Build Tool: Vite
└── Testing: Vitest + Playwright
```

**Rationale:**
1. **React over Vue** - Better ecosystem for graph libraries, more community resources
2. **Tauri over Electron** - Smaller bundles, better performance, native feel
3. **Zustand over Redux** - Simpler API, less boilerplate for medium-complexity state
4. **Radix UI** - Accessible, unstyled primitives that work great with Tailwind

**Alternative Stack (simpler, faster to implement):**
```
├── Keep Vue 3 (existing)
├── Replace components with force-graph
├── Add Electron wrapper later
└── Desktop app as Phase 2
```

---

## 4. UI/UX Design Specification

### 4.1 Layout Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  Header Bar                                                          │
│  [Logo] [Search] [Filter] [View Mode] [Settings] [Session: X]       │
├───────────────┬───────────────────────────────────────┬─────────────┤
│               │                                       │             │
│  Tools Panel  │      Force-Directed Graph Canvas      │  Details    │
│  (Collapsible)│                                       │   Panel     │
│               │                                       │             │
│  [Filter]     │         ┌───┐                        │  Node:      │
│  [Highlight]  │        /│ A │\                       │  - Name     │
│  [Clusters]   │       / └───┘ \                      │  - Type     │
│  [Pathways]   │  ┌───┐         ┌───┐                 │  - File     │
│  [Webhooks]   │  │ B │─────────│ C │                 │  - Complexity│
│  [Sessions]   │  └───┘         └───┘                 │  - Metadata │
│               │       \       /                      │             │
│               │        \┌───┐/                       │  [Annotate] │
│               │         │ D │                        │  [Navigate] │
│               │         └───┘                        │             │
│               │                                       │             │
├───────────────┴───────────────────────────────────────┴─────────────┤
│  Status Bar: [Nodes: 974] [Edges: 12,767] [WebSocket: ●] [CPU: 23%] │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 Tools Panel Components

#### 4.2.1 Filter Panel
```typescript
interface FilterOptions {
  // Node filters
  nodeTypes: ('function' | 'class' | 'module' | 'method')[];
  languages: string[];  // ['python', 'typescript', 'c#']
  complexityRange: [number, number];  // [min, max]
  
  // Relationship filters
  relationshipTypes: ('calls' | 'contains' | 'imports' | 'seam')[];
  includeSeams: boolean;
  
  // Search
  namePattern: string;  // regex or glob
  filePattern: string;
  
  // Graph structure
  minDegree: number;  // Show only nodes with N+ connections
  maxDepth: number;   // Limit traversal depth
}
```

#### 4.2.2 Highlight & Regions
```typescript
interface HighlightOptions {
  // Highlight modes
  mode: 'single' | 'connected' | 'cluster' | 'pathway';
  
  // Colors
  primaryColor: string;
  secondaryColor: string;
  fadeOthers: boolean;
  
  // Animation
  pulseEffect: boolean;
  trailEffect: boolean;  // For pathway traversal
}

interface Region {
  id: string;
  name: string;
  color: string;
  nodeIds: string[];
  isAutoDetected: boolean;  // From clustering algorithm
}
```

#### 4.2.3 Pathway Analyzer
```typescript
interface PathwayAnalysis {
  startNodeId: string;
  endNodeId?: string;  // Optional for exploration mode
  
  // Analysis modes
  mode: 'call-chain' | 'data-flow' | 'shortest-path' | 'all-paths';
  
  // Constraints
  maxHops: number;
  mustPassThrough: string[];  // Node IDs
  avoidNodes: string[];
  
  // Output
  paths: NodePath[];
  statistics: {
    totalPaths: number;
    avgLength: number;
    criticalNodes: string[];  // Nodes on most paths
  };
}
```

#### 4.2.4 Webhook Observer (MCP Session Tracker)
```typescript
interface WebhookObserver {
  // Connection
  websocketUrl: string;
  status: 'connected' | 'disconnected' | 'connecting';
  
  // Event subscriptions
  eventTypes: ('node_added' | 'node_visited' | 'traversal_start' | 'traversal_end')[];
  
  // Session tracking
  currentSession: {
    id: string;
    startTime: Date;
    visitedNodes: string[];
    currentNode: string | null;
  };
  
  // Visualization
  highlightVisited: boolean;
  showTraversalAnimation: boolean;
  recordHistory: boolean;
}
```

### 4.3 Details Panel Components

#### 4.3.1 Node Metadata Viewer
```typescript
interface NodeDetails {
  // Core info
  id: string;
  name: string;
  nodeType: string;
  language: string;
  
  // Location
  filePath: string;
  startLine: number;
  endLine: number;
  
  // Metrics
  complexity: number;
  lineCount: number;
  inDegree: number;
  outDegree: number;
  
  // Documentation
  docstring: string;
  
  // Relationships
  callers: NodeSummary[];
  callees: NodeSummary[];
  imports: NodeSummary[];
  
  // User annotations
  annotations: Annotation[];
}
```

#### 4.3.2 Annotation Editor
```typescript
interface Annotation {
  id: string;
  nodeId: string;
  
  // Content
  title: string;
  content: string;  // Markdown-enabled rich text
  tags: string[];
  
  // Metadata
  createdAt: Date;
  updatedAt: Date;
  author: string;
  
  // Visibility
  isPrivate: boolean;
  linkedAnnotations: string[];  // Related annotation IDs
}

interface AnnotationEditor {
  // Rich text capabilities
  markdownSupport: boolean;
  codeHighlighting: boolean;
  linkToNodes: boolean;
  attachments: boolean;
  
  // Organization
  tagAutocomplete: boolean;
  searchAnnotations: boolean;
  exportAnnotations: boolean;
}
```

---

## 5. Implementation Roadmap

### Phase 1: Core Graph Visualization (2-3 weeks)

**Week 1: Foundation**
- [ ] Set up new React + TypeScript project with Vite
- [ ] Configure Tailwind CSS and Radix UI
- [ ] Integrate force-graph library
- [ ] Connect to existing HTTP API
- [ ] Basic graph rendering with node/edge display

**Week 2: Interactivity**
- [ ] Node selection and details panel
- [ ] Pan/zoom controls
- [ ] Basic filtering (by type, language)
- [ ] Search functionality
- [ ] Node highlighting

**Week 3: Polish**
- [ ] Performance optimization for large graphs
- [ ] Responsive layout
- [ ] Loading states and error handling
- [ ] Basic keyboard navigation

### Phase 2: Tools Panel (2 weeks)

**Week 4: Filtering & Highlighting**
- [ ] Advanced filter panel UI
- [ ] Region/cluster detection
- [ ] Pathway visualization
- [ ] Color customization

**Week 5: MCP Integration**
- [ ] WebSocket connection to CDC events
- [ ] Session tracking visualization
- [ ] Real-time node highlighting
- [ ] Traversal animation

### Phase 3: Annotations & Metadata (1-2 weeks)

**Week 6: Rich Details**
- [ ] Enhanced node details panel
- [ ] Source code preview integration
- [ ] Annotation CRUD operations
- [ ] Markdown editor for annotations

**Week 7: Advanced Features**
- [ ] Annotation search and filtering
- [ ] Export/import annotations
- [ ] Linked annotations between nodes
- [ ] Tag management

### Phase 4: Desktop App (Optional, 1-2 weeks)

**Week 8: Tauri Integration**
- [ ] Tauri project setup
- [ ] Native file system access
- [ ] Desktop-specific features
- [ ] Build and distribution

---

## 6. Backend Enhancements Needed

### 6.1 New API Endpoints

```python
# /api/graph/export - Full graph export for visualization
@router.get("/export")
async def export_full_graph(
    limit: int = Query(10000),
    include_metadata: bool = Query(True)
) -> GraphExportResponse:
    """Export nodes and relationships for force-graph visualization."""
    pass

# /api/graph/clusters - Auto-detect clusters
@router.get("/clusters")
async def detect_clusters(
    algorithm: str = Query("louvain")  # louvain, label_propagation, etc.
) -> ClustersResponse:
    """Detect clusters/communities in the graph."""
    pass

# /api/graph/path - Path finding
@router.get("/path/{from_node}/{to_node}")
async def find_path(
    from_node: str,
    to_node: str,
    algorithm: str = Query("dijkstra")
) -> PathResponse:
    """Find shortest path between two nodes."""
    pass

# /api/annotations - Annotation CRUD
@router.post("/annotations")
async def create_annotation(annotation: AnnotationCreate) -> Annotation:
    pass

@router.get("/annotations/{node_id}")
async def get_annotations(node_id: str) -> List[Annotation]:
    pass
```

### 6.2 WebSocket Enhancements

```python
# Enhanced CDC events for MCP session tracking
class MCPSessionEvent:
    session_id: str
    event_type: Literal['session_start', 'session_end', 'node_visit', 'tool_call']
    node_id: Optional[str]
    timestamp: datetime
    metadata: Dict[str, Any]
```

---

## 7. Data Models

### 7.1 Graph Export Format

```typescript
interface GraphExport {
  nodes: {
    id: string;
    name: string;
    type: string;
    language: string;
    complexity: number;
    file: string;
    line: number;
    metadata: Record<string, unknown>;
  }[];
  
  links: {
    source: string;
    target: string;
    type: string;
    isSeam: boolean;
    weight?: number;
  }[];
  
  clusters?: {
    id: string;
    name: string;
    color: string;
    nodeIds: string[];
  }[];
  
  stats: {
    totalNodes: number;
    totalLinks: number;
    languages: Record<string, number>;
    avgComplexity: number;
  };
}
```

### 7.2 Force-Graph Node Format

```typescript
interface ForceGraphNode {
  id: string;
  
  // Display
  name: string;
  val: number;  // Node size
  color: string;
  
  // Custom data
  nodeType: string;
  language: string;
  complexity: number;
  cluster?: string;
  
  // State
  fx?: number;  // Fixed X position
  fy?: number;  // Fixed Y position
  highlighted?: boolean;
}

interface ForceGraphLink {
  source: string;
  target: string;
  
  // Display
  color: string;
  width: number;
  curvature: number;
  
  // Custom data
  type: string;
  isSeam: boolean;
}
```

---

## 8. Performance Considerations

### 8.1 Large Graph Optimization

| Technique | Impact | Implementation |
|-----------|--------|----------------|
| **WebGL rendering** | 10x faster for 10K+ nodes | Use force-graph's WebGL mode |
| **Node clustering** | Reduce visual complexity | Server-side clustering API |
| **Level of detail** | Show detail on zoom | Hide labels at distance |
| **Virtual scrolling** | Fast list rendering | Virtualize details panels |
| **Incremental loading** | Faster initial render | Load visible nodes first |
| **Web Workers** | Non-blocking layout | Offload force simulation |

### 8.2 Memory Management

```typescript
// Dispose pattern for large graphs
class GraphManager {
  private graph: ForceGraph;
  private containerRef: HTMLElement;
  
  dispose() {
    // Clear graph data first
    this.graph.graphData({ nodes: [], links: [] });
    // Remove the canvas element and recreate if needed
    // Note: force-graph doesn't expose a public destructor - 
    // the recommended pattern is to clear data and let garbage collection handle cleanup
    this.containerRef.innerHTML = '';
  }
  
  // Limit active nodes
  async loadSubgraph(centerNode: string, depth: number) {
    const subgraph = await api.getSubgraph(centerNode, depth);
    this.graph.graphData(subgraph);
  }
}
```

---

## 9. Technology Dependencies

### 9.1 Core Dependencies

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "force-graph": "^1.51.0",
    "3d-force-graph": "^1.73.0",
    "@radix-ui/react-dialog": "^1.0.5",
    "@radix-ui/react-dropdown-menu": "^2.0.6",
    "@radix-ui/react-tabs": "^1.0.4",
    "@radix-ui/react-tooltip": "^1.0.7",
    "@radix-ui/react-slider": "^1.1.2",
    "zustand": "^4.5.0",
    "react-markdown": "^9.0.0",
    "prismjs": "^1.29.0",
    "@tanstack/react-query": "^5.0.0",
    "tailwindcss": "^3.4.0"
  },
  "devDependencies": {
    "@tauri-apps/cli": "^1.5.0",
    "vite": "^5.0.0",
    "typescript": "^5.3.0",
    "vitest": "^1.0.0",
    "@playwright/test": "^1.40.0"
  }
}
```

### 9.2 Security Considerations

- [ ] No direct filesystem access from browser (use Tauri APIs)
- [ ] Sanitize all user-provided annotation content
- [ ] Rate limit API endpoints
- [ ] Validate WebSocket messages

---

## 10. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Initial load time | <2s for 10K nodes | Performance API |
| Interaction responsiveness | <100ms response | Frame timing |
| Memory usage | <500MB for 50K nodes | DevTools profiling |
| WebSocket latency | <50ms event delivery | Timestamp comparison |
| Annotation save time | <500ms | API response time |

---

## 11. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Force-graph performance limits | Medium | High | Implement clustering, LOD |
| WebSocket disconnections | Low | Medium | Auto-reconnect with backoff |
| Tauri compatibility issues | Low | Medium | Electron fallback |
| API changes breaking frontend | Medium | Low | Version API, contract tests |

---

## 12. Decision Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Graph Library | **force-graph** | Already installed, performant, flexible |
| Frontend Framework | **React + TypeScript** | Better ecosystem, cleaner state management |
| UI Components | **Radix UI + Tailwind** | Accessible, customizable, consistent |
| Desktop Wrapper | **Tauri** | Small bundles, modern architecture |
| State Management | **Zustand** | Simple API, good React integration |
| Backend Changes | **Minimal** | Reuse existing API, add export/annotations |

---

## Appendix A: File Structure

```
frontend-v2/
├── src/
│   ├── components/
│   │   ├── graph/
│   │   │   ├── ForceGraph.tsx
│   │   │   ├── GraphControls.tsx
│   │   │   └── NodeTooltip.tsx
│   │   ├── panels/
│   │   │   ├── ToolsPanel.tsx
│   │   │   ├── DetailsPanel.tsx
│   │   │   ├── FilterPanel.tsx
│   │   │   └── AnnotationEditor.tsx
│   │   └── layout/
│   │       ├── Header.tsx
│   │       ├── StatusBar.tsx
│   │       └── SplitPane.tsx
│   ├── hooks/
│   │   ├── useGraph.ts
│   │   ├── useWebSocket.ts
│   │   └── useAnnotations.ts
│   ├── stores/
│   │   ├── graphStore.ts
│   │   ├── filterStore.ts
│   │   └── sessionStore.ts
│   ├── api/
│   │   ├── graphApi.ts
│   │   └── annotationsApi.ts
│   ├── types/
│   │   └── index.ts
│   └── App.tsx
├── public/
├── src-tauri/  (for desktop)
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── tsconfig.json
```

---

## Appendix B: Existing Code to Preserve/Adapt

The following code from the existing frontend can be adapted:

1. **Type definitions** (`frontend/src/types/graph.ts`) - Reuse interfaces
2. **API client** (`frontend/src/api/graphClient.ts`) - Adapt to React Query
3. **WebSocket client** (`frontend/src/api/eventsClient.ts`) - Refactor for React hooks
4. **Filter logic** (`frontend/src/stores/filterStore.ts`) - Migrate to Zustand

---

*Document created for CodeNavigator force-directed graph visualization planning.*
