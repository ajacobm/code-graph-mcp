# Session 9: Force Graph & UX Redesign Implementation

**Date**: 2025-11-07  
**Status**: ⚠️ IN PROGRESS - Components created, needs type fixes and testing  
**Duration**: ~2 hours

## Objectives

1. ✅ Research force-graph library (2D & 3D options)
2. ✅ Create simplified "signpost" navigation components
3. ✅ Implement 2D force-graph visualization
4. ✅ Redesign App.vue layout with proper tab switching
5. ⬜ Fix TypeScript type errors
6. ⬜ Test in browser with Playwright

## Components Created

### 1. NodeTile.vue (NEW)
**Purpose**: Reusable tile component for displaying nodes with "signpost" metaphor

**Features**:
- Visual icons based on node type (🚀 entry, 🔀 hub, 🍃 leaf)
- Direction indicators (🔵 inbound, 🟢 outbound, 🟡 sibling)
- Distance/hop display with color coding (yellow=same file, green=nearby, red=far)
- Complexity and language badges
- Hover effects with slide animation
- Border colors by relationship direction

**Props**:
- `node: any` - Node data
- `distance?: number` - Hop count from current node
- `direction?: 'inbound' | 'outbound' | 'sibling'`
- `showDistance?: boolean`

**Emits**:
- `click: [node]` - When tile is clicked

### 2. ConnectionsList.vue (NEW)
**Purpose**: "Signpost-style" navigation view showing node connections

**Features**:
- "You are here" card with current node stats
- Three categorized sections:
  - ↑ CALLED BY (callers/parents)
  - ↓ CALLS (callees/children)
  - ── SIBLINGS (same file)
- Distance calculation for each connection
- Auto-loads callers/callees via API
- Filters siblings to first 5 with "show more" indicator
- Loading and error states
- Empty state handling

**API Integration**:
- `GET /api/graph/query/callers?symbol={name}`
- `GET /api/graph/query/callees?symbol={name}`
- Local filtering for siblings (same file_path)

### 3. ForceGraphViewer.vue (NEW)
**Purpose**: 2D force-directed graph visualization using `force-graph` library

**Features**:
- Canvas-based rendering (handles 500+ nodes smoothly)
- Node coloring by type (function, class, module, import)
- Node sizing by complexity
- Special node borders (entry points, hubs, leaves)
- Link coloring by relationship type (calls, imports, contains)
- Interactive highlighting on hover
- Directional arrows on links
- Particle flow animation on highlighted links
- Click to select nodes
- Fit-to-view button
- Legend overlay
- Hover info panel
- Responsive to window resize

**Force Physics Configuration**:
```javascript
.d3Force('charge', d3.forceManyBody().strength(-120))
.d3Force('link', d3.forceLink().distance(50))
```

**Props**:
- `graphData: GraphData` - Nodes and relationships
- `selectedNodeId?: string | null` - Currently selected node

**Emits**:
- `nodeClick: [node]` - When node is clicked
- `nodeHover: [node | null]` - When node is hovered

**Exposed Methods**:
- `fitView()` - Zoom to fit all nodes
- `zoomToNode(nodeId)` - Center and zoom to specific node

### 4. App.vue (REDESIGNED)
**Purpose**: Main application layout with cleaner tab-based navigation

**New Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│ Header: Logo + Stats + Re-analyze + Search                 │
├─────────────────────────────────────────────────────────────┤
│ Tabs: Force Graph | Connections | Browse | Entry Points... │
├─────────────────────────────────────────────────┬───────────┤
│                                                 │           │
│  Main Panel (switches based on active tab)     │  Right    │
│                                                 │  Sidebar  │
│  - Force Graph (ForceGraphViewer)              │  (Node    │
│  - Connections (ConnectionsList)               │  Details) │
│  - Browse Nodes (NodeBrowser)                  │           │
│  - Entry Points (EntryPointExplorer)           │  Only     │
│  - Query Tools (ToolPanel)                     │  when     │
│                                                 │  node     │
│                                                 │  selected │
└─────────────────────────────────────────────────┴───────────┘
```

**Key Improvements**:
- Removed left sidebar (was cluttered)
- Main content actually switches with tabs (was broken)
- Stats panel collapsible in header
- Re-analyze button prominent in header
- Right sidebar only shows when node is selected
- Cleaner visual hierarchy

**New Tabs**:
1. **Force Graph** (🌐) - 2D force-directed visualization
2. **Connections** (🔗) - Signpost list view
3. **Browse Nodes** (📂) - Category browser
4. **Entry Points** (🚀) - Entry point explorer
5. **Query Tools** (🔍) - Symbol query tools

## Dependencies Added

```bash
npm install force-graph
```

**Library Details**:
- **force-graph**: 2D force-directed graph on HTML5 canvas
- Uses d3-force for physics simulation
- Supports 1000+ nodes with smooth performance
- Built-in zoom, pan, drag interactions
- Event handlers for click, hover, drag
- Customizable rendering via canvas API

## Store Enhancements

### graphStore.ts

**New Methods**:

1. `loadFullGraph()` - Load all nodes and initial relationships
   - Gets all nodes via search('')
   - Loads subgraph for first 100 nodes
   - Populates nodes and edges Maps

2. `reanalyze()` - Trigger backend re-analysis
   - POST to `/api/graph/admin/reanalyze`
   - Reloads graph data after completion
   - Updates stats

## Type Definitions Added

### types/graph.ts

**New Types**:
```typescript
export interface GraphData {
  nodes: Node[]
  relationships: Edge[]
}
```

## Known Issues / TODO

### Type Errors (needs fixing)
1. ❌ NodeResponse doesn't have `node_type` or `location` fields
   - API returns different structure than types expect
   - Need to update types or add mapping layer

2. ❌ getSubgraph expects single nodeId, not array
   - Current code tries to pass array of 100 node IDs
   - Need to either:
     - Call getSubgraph multiple times
     - Use different endpoint
     - Pass first node only

3. ❌ SearchResultResponse has `results` not `nodes`
   - Already fixed in code
   - Types are correct

### Missing Features
1. ⬜ Navigation from graph to connections view
   - Click node in force graph → show in connections list
   - Currently just sets selectedNodeId

2. ⬜ Breadcrumb navigation
   - Track visited nodes
   - Allow going back

3. ⬜ Distance calculation
   - Currently using result order as distance
   - Should use actual BFS/shortest path

4. ⬜ Component library / POC page
   - Test components in isolation
   - Good for future development

## Files Modified

**Created (4 files)**:
- `frontend/src/components/NodeTile.vue` (125 lines)
- `frontend/src/components/ConnectionsList.vue` (215 lines)
- `frontend/src/components/ForceGraphViewer.vue` (295 lines)
- `frontend/src/App.vue` (REDESIGNED, 220 lines)

**Modified (3 files)**:
- `frontend/src/stores/graphStore.ts` (+75 lines)
- `frontend/src/types/graph.ts` (+6 lines)
- `frontend/package.json` (+32 packages)

**Total**:
- Lines added: ~940
- New components: 3
- Dependencies added: 1 (force-graph)

## Next Steps

### Immediate (Fix & Test)
1. **Fix type errors** in graphStore.ts
   - Update NodeResponse type to match API
   - Fix getSubgraph call (use single node or multiple calls)
   - Test with actual API

2. **Test in browser**
   - Use Playwright to verify UI loads
   - Test force graph rendering
   - Test connections list loading
   - Verify tab switching works

3. **Fix API/type mismatches**
   - Map API responses to internal types
   - Add transformation layer if needed

### Near-term (Enhancements)
4. **Add navigation flow**
   - Click node in graph → switch to connections tab
   - Click tile in connections → update selected node
   - Add "back" button

5. **Add distance calculation**
   - Implement BFS for hop counting
   - Add to backend API if needed
   - Show actual shortest path

6. **Improve UX**
   - Add loading skeletons
   - Add empty states
   - Add error recovery
   - Add keyboard navigation

### Future (Advanced Features)
7. **3D Force Graph** (if 2D works well)
   - Install `3d-force-graph`
   - Add as separate tab or mode
   - Use Three.js for rendering
   - Camera controls and animations

8. **Component Library Page**
   - Create `/poc` route
   - Showcase all components
   - Interactive props playground
   - Use for development/testing

9. **Performance Optimization**
   - Lazy load graph data
   - Virtualize long lists
   - Web Worker for calculations
   - Progressive rendering

## API Endpoints Used

**Existing**:
- `GET /api/graph/stats` - Graph statistics
- `GET /api/graph/nodes/search?query={q}` - Search nodes
- `GET /api/graph/query/callers?symbol={name}` - Find callers
- `GET /api/graph/query/callees?symbol={name}` - Find callees
- `POST /api/graph/subgraph` - Get focused subgraph
- `POST /api/graph/admin/reanalyze` - Force re-analysis

**Needed** (for distance calculation):
- `GET /api/graph/path?from={id}&to={id}` - Shortest path
- `GET /api/graph/node/{id}/distance?to={id}` - Hop count

## Testing Strategy

### Manual Testing (Playwright)
1. Navigate to http://localhost:5173
2. Verify force graph loads and renders
3. Click nodes and verify selection
4. Switch tabs and verify content changes
5. Click re-analyze and verify it works
6. Test connections list with selected node
7. Verify responsive behavior

### Integration Testing
1. Test API connectivity
2. Test data loading
3. Test error handling
4. Test performance with 500+ nodes

## Design Philosophy

### "Code Geography" Metaphor
Instead of graph theory concepts (nodes, edges, traversal), we use geographical metaphors:

- **📍 You are here** → Current node
- **Distance indicators** → Hop counts like road signs ("Paris 1024km")
- **Direction arrows** → ↑ upstream (callers), ↓ downstream (callees)
- **Neighborhoods** → Siblings in same file
- **Map view** → Force graph overview

### Progressive Disclosure
- Start with simple list view (connections)
- Add graph visualization as enhancement
- Keep 3D as optional advanced feature
- Don't overwhelm with all data at once

### Performance First
- Use canvas (force-graph) not DOM (cytoscape)
- Limit initial load to 100 nodes
- Lazy load on demand
- Virtualize long lists
- Debounce expensive operations

## Lessons Learned

1. **force-graph is perfect for this use case**
   - Much faster than Cytoscape.js
   - Simpler API
   - Better for 500+ nodes
   - Canvas-based = smooth performance

2. **Type safety is crucial**
   - API types must match actual responses
   - Add transformation layer early
   - Use strict TypeScript settings

3. **Layout matters**
   - Three-panel split is cleaner than sidebars
   - Tabs must actually switch content
   - Right sidebar only when needed
   - Header for global actions

4. **Metaphors help UX**
   - "Signpost" is more intuitive than "graph traversal"
   - "Distance" is clearer than "BFS depth"
   - Emojis add personality and quick recognition

## References

- force-graph: https://github.com/vasturiano/force-graph
- 3d-force-graph: https://github.com/vasturiano/3d-force-graph
- Design proposal: `/home/adam/GitHub/code-graph-mcp/docs/REDESIGN_PROPOSAL.md`
- Context7 docs: `/vasturiano/force-graph` and `/vasturiano/3d-force-graph`
