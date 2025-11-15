# Session 2: Vue3 UI & Graph Visualization

**Duration**: 1-2 sessions  
**Status**: 📋 Planned  
**Branch**: `feature/graph-ui-vue` (from `feature/rest-api-graph-queries`)

## Overview
Build interactive Vue 3 + Cytoscape.js visualization for code graphs with filtering, search, and drill-down navigation.

## Tech Stack

- **Framework**: Vue 3 (Composition API)
- **Visualization**: Cytoscape.js (DAG layout, optimized for call graphs)
- **HTTP Client**: axios + vue-query/TanStack Query
- **State**: Pinia (store management)
- **Build**: Vite
- **Styling**: Tailwind CSS

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── GraphViewer.vue       (main visualization, Cytoscape)
│   │   ├── NodeDetails.vue       (right panel, node info + callers/callees)
│   │   ├── SearchBar.vue         (find nodes/relationships)
│   │   ├── FilterPanel.vue       (language, type, complexity filters)
│   │   └── CallChainTracer.vue   (step through call sequences)
│   ├── stores/
│   │   ├── graphStore.ts         (graph data, loading states)
│   │   └── filterStore.ts        (active filters)
│   ├── api/
│   │   └── graphClient.ts        (axios wrapper for /api/graph/*)
│   ├── types/
│   │   └── graph.ts              (TypeScript interfaces)
│   └── App.vue
├── package.json
└── vite.config.ts
```

## Key Components

### GraphViewer.vue
- Load graph from `/api/graph/traverse` or `/api/graph/call-chain/{node}`
- Render with Cytoscape.js (hierarchical DAG layout)
- Visual distinction for SEAM edges (dashed, red color)
- Click node → select in NodeDetails
- Hover → tooltip with name + complexity + language

### NodeDetails.vue
- Full node metadata (location, docstring, complexity)
- Lists incoming relationships (find_callers equivalent)
- Lists outgoing relationships (find_callees equivalent)
- Button: "Trace to entry point" (navigate to root)
- Copy node ID to clipboard

### CallChainTracer.vue
- Step-by-step visual navigation
- Entry → Step 1 → Step 2 → ... → Exit
- Each step shows SEAM crossings (language changes)
- Controls: Previous/Next/Reset
- Export chain as JSON

### FilterPanel.vue
- Multi-select languages (Python, JavaScript, C#, SQL, etc)
- Node type filter (function, class, etc)
- Toggle: "SEAM relationships only"
- Complexity slider (0-50)
- Apply/Clear buttons

### SearchBar.vue
- Autocomplete search by node name
- "Find in current graph" vs "Search all nodes"
- Results shown in dropdown with language badge

## API Integration (graphClient.ts)

```typescript
export class GraphClient {
  async getStats()
  async getNode(nodeId: string)
  async traverse(startNode, queryType, maxDepth, includeSeams)
  async searchNodes(name, language, nodeType, limit)
  async getSeams(limit)
  async getCallChain(startNode, followSeams, maxDepth)
}
```

## State Management (Pinia)

```typescript
interface GraphState {
  nodes: Map<string, Node>
  edges: Map<string, Edge>
  selectedNodeId: string | null
  isLoading: boolean
  error: string | null
  viewMode: 'full' | 'call_chain' | 'seams_only'
  stats: GraphStats
}

interface FilterState {
  languages: string[]
  nodeTypes: string[]
  seamOnly: boolean
  complexityRange: [number, number]
}
```

## Tasks

### 2.1 Project Setup
- [ ] `npm create vite@latest frontend -- --template vue-ts`
- [ ] Install deps: axios, cytoscape, pinia, tailwindcss
- [ ] Configure Vite for proxy to localhost:8000 (/api/*)
- [ ] TypeScript config for strict mode

### 2.2 API Layer
- [ ] Create `src/api/graphClient.ts` with typed axios calls
- [ ] Create `src/types/graph.ts` (interfaces matching response DTOs)
- [ ] Error handling + loading states

### 2.3 Store Setup
- [ ] `src/stores/graphStore.ts` (Pinia)
- [ ] `src/stores/filterStore.ts` (Pinia)
- [ ] Actions for loadGraph, selectNode, applyFilters

### 2.4 Components
- [ ] **GraphViewer.vue** - Cytoscape initialization + layout
- [ ] **NodeDetails.vue** - Node panel with incoming/outgoing edges
- [ ] **FilterPanel.vue** - Reactive filter controls
- [ ] **SearchBar.vue** - Auto-complete search
- [ ] **CallChainTracer.vue** - Step-through navigation

### 2.5 Integration & Styling
- [ ] Responsive layout (header + sidebar + main + detail panel)
- [ ] Tailwind styling
- [ ] Light/dark mode toggle
- [ ] Loading spinners, error messages

### 2.6 Testing
- [ ] Component mount tests
- [ ] API client mocking
- [ ] User interaction flows (select node, filter, search)

## Deliverables

- [ ] Vue 3 project runs on localhost:5173
- [ ] Connects to API on localhost:8000
- [ ] Graph renders 100+ nodes smoothly (60 FPS)
- [ ] SEAM edges visually distinct
- [ ] Node click → details panel updates
- [ ] Filter by language/type reduces graph
- [ ] Call chain tracer navigable
- [ ] Responsive on 1366+ width
- [ ] Error handling for missing nodes/network failures

## Performance Targets

- First load: < 2 seconds for typical graph
- Node selection: < 100ms UI update
- Filter apply: < 500ms graph re-render
- Cytoscape pan/zoom: 60 FPS

## Known Dependencies

- `/api/graph/*` endpoints must be working (Session 1)
- CORS enabled on FastAPI (already done)
- Redis optional (caching for large graphs)

## Success Criteria

- Interactive visualization of multi-tier code graphs
- Users can trace calls across languages visually
- SEAM relationships clearly marked
- Filtering reduces complexity intelligently
- No missing API responses or 500 errors
