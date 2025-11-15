# Frontend UX Redesign Proposal

⚠️ **STATUS: NEEDS REVIEW & UPDATE**

**Issues to address**:
- ❌ Remove mobile-first responsive design emphasis (not applicable to code graph navigation)
- ⚠️ Clarify WebSocket usage (currently emitting events but not used in UI)
- ✅ Confirm Cytoscape.js graph visualization approach
- ✅ Verify Vue 3 + Vite toolchain expectations
- 📋 Define how real-time node highlighting integrates with traversal events

**Last Updated**: Session 19 (November 15, 2025)  
**Next Review**: Before feature/ui-redesign branch creation

---

## Philosophy: "Code Geography" Navigation

Instead of forcing users to understand graph theory, we'll use a **geographical metaphor**:
- **You are here** → Current node being viewed
- **Nearby** → Direct connections (parents, children, siblings)
- **Signposts** → Distant but important nodes with "distance" metrics
- **Map** → Overview of the codebase structure

## Layout Architecture

### New Three-Panel Design

```
┌─────────────────────────────────────────────────────────────┐
│ Header: Search + Stats + Re-analyze Button                 │
├──────────────┬──────────────────────────────┬───────────────┤
│              │                              │               │
│  Left Panel  │      Main Content           │  Right Panel  │
│  (240px)     │      (flex-1)               │  (320px)      │
│              │                              │               │
│  Navigation  │  • Node Browser             │  Minimap/     │
│  Tree        │  • Node Details             │  Metadata     │
│              │  • Connections List         │  Panel        │
│              │  • Query Results            │               │
│              │                              │               │
└──────────────┴──────────────────────────────┴───────────────┘
```

### Left Panel: **Navigation Tree**
- Collapsible file/module hierarchy (like VS Code)
- Quick filters (entry points, hubs, leaves)
- Recent nodes visited
- Saved bookmarks

### Main Panel: **Content Area** (switches based on selection)
1. **Node Details View** (when node selected)
2. **Connections List** (vertical tile list with signposts)
3. **Search Results**
4. **Entry Points Dashboard**

### Right Panel: **Context & Actions**
- Node metadata (type, complexity, language)
- Quick stats (callers/callees counts)
- Action buttons (trace, bookmark, copy)
- Mini-dependency preview

## Main Content: Connection List Design

### "Signpost" Metaphor Implementation

```
┌────────────────────────────────────────────────────────┐
│ 📍 You are here: cache_manager.py                     │
├────────────────────────────────────────────────────────┤
│                                                        │
│ ↑ CALLED BY (Parents - 3 nodes)                       │
│ ┌──────────────────────────────────────────────┐     │
│ │ 🔵 UniversalAnalysisEngine.__init__()        │     │
│ │    └─ server/analysis_engine.py              │     │
│ │    └─ 12 hops away · Complexity 45           │     │
│ └──────────────────────────────────────────────┘     │
│                                                        │
│ ┌──────────────────────────────────────────────┐     │
│ │ 🔵 initialize_cache()                        │     │
│ │    └─ redis_cache.py                         │     │
│ │    └─ 8 hops away · Complexity 23            │     │
│ └──────────────────────────────────────────────┘     │
│                                                        │
│ ↓ CALLS (Children - 5 nodes)                          │
│ ┌──────────────────────────────────────────────┐     │
│ │ 🟢 redis.asyncio.Redis                       │     │
│ │    └─ External library                       │     │
│ │    └─ Direct dependency                      │     │
│ └──────────────────────────────────────────────┘     │
│                                                        │
│ ── SIBLINGS (Same file - 19 nodes)                    │
│ ┌──────────────────────────────────────────────┐     │
│ │ 🟡 FileMetadata.from_path()                  │     │
│ │    └─ Same module                            │     │
│ │    └─ 0 hops away                            │     │
│ └──────────────────────────────────────────────┘     │
│                                                        │
│ 🗺️  FAR CONNECTIONS (>10 hops - 24 nodes)            │
│ ┌──────────────────────────────────────────────┐     │
│ │ 🔴 GraphAPIServer.startup()                  │     │
│ │    └─ http_server.py                         │     │
│ │    └─ Paris: 1024 km → Berlin: 1400 km      │     │
│ │    (18 hops via UniversalGraph)              │     │
│ └──────────────────────────────────────────────┘     │
└────────────────────────────────────────────────────────┘
```

### Distance Metrics (Signpost Numbers)

Instead of abstract graph theory:
- **0 hops** → Same file/module (siblings)
- **1 hop** → Direct caller/callee
- **2-5 hops** → Nearby (show path preview)
- **6-10 hops** → Medium distance
- **>10 hops** → Far away (show "via X intermediate nodes")

### Visual Encoding

**Color by Relationship Type**:
- 🔵 Blue → Callers (incoming)
- 🟢 Green → Callees (outgoing)
- 🟡 Yellow → Siblings (same file)
- 🔴 Red → Far/indirect connections
- 🟣 Purple → Cross-language seams

**Size by Importance**:
- Large tile → High complexity OR entry point OR hub
- Medium → Normal functions
- Small → Utilities/imports

**Icons**:
- 🚀 Entry point (no callers)
- 🔀 Hub (highly connected)
- 🍃 Leaf (no callees)
- 🌉 Seam (cross-language)

## Alternative: Simple 3D Visualization

If we want to keep some visual representation, consider **lightweight 3D options**:

### Option A: Force Graph 3D (React/Vue compatible)
```bash
npm install 3d-force-graph-vr
# OR
npm install force-graph
```

**Pros**:
- Interactive 3D navigation
- Handles 500+ nodes smoothly
- WebGL-based (fast)
- Click nodes to focus
- Auto-layout with physics

**Example**:
```javascript
import ForceGraph3D from '3d-force-graph-vr'

const graph = ForceGraph3D()(elem)
  .graphData({ nodes, links })
  .nodeLabel('name')
  .nodeColor(node => nodeColorByType(node))
  .onNodeClick(node => showNodeDetails(node))
```

### Option B: vis-network 3D
```bash
npm install vis-network vis-data
```

**Pros**:
- 2D/3D modes
- Built-in clustering
- Hierarchical layouts
- Good for 100-1000 nodes

### Option C: Plotly.js 3D Scatter
```bash
npm install plotly.js-dist-min
```

**Pros**:
- Simple 3D scatter plots
- Each node = point in 3D space
- Fast rendering
- Good for exploration

## Recommended Implementation Plan

### Phase 1: Simplify Current UI (1-2 days)

1. **Remove Cytoscape graph** (shelve for later)
2. **Implement Connection List view** with signpost metaphor
3. **Fix tab navigation** to actually switch main content
4. **Add breadcrumbs** for navigation history
5. **Improve tile styling** with proper DaisyUI components

### Phase 2: Add Tree Navigation (1 day)

1. **File tree** in left panel (collapsible hierarchy)
2. **Quick filters** (entry/hub/leaf toggle buttons)
3. **Recent nodes** history stack
4. **Bookmarks** system

### Phase 3: Enhanced Metadata (1 day)

1. **Distance calculations** (BFS for hop counts)
2. **Path highlighting** (show intermediate nodes)
3. **Complexity indicators** (visual bars)
4. **Stats dashboard** (total nodes, edges, languages)

### Phase 4: Optional 3D Visualization (2-3 days)

Only if Phase 1-3 work well:
1. Add Force Graph 3D library
2. Create separate "3D Explorer" tab
3. Link to connection list (click node → show details)
4. Make it optional/skippable

## Technical Changes Needed

### File Structure
```
frontend/src/
├── components/
│   ├── ConnectionsList.vue      (NEW - signpost list)
│   ├── NavigationTree.vue       (NEW - file tree)
│   ├── NodeTile.vue            (NEW - reusable tile)
│   ├── BreadcrumbNav.vue       (NEW - navigation history)
│   ├── StatsPanel.vue          (NEW - right sidebar)
│   ├── NodeDetails.vue         (KEEP - enhance)
│   ├── SearchBar.vue           (KEEP - enhance)
│   └── GraphViewer.vue         (SHELVE - optional later)
├── stores/
│   ├── navigationStore.ts      (NEW - history, breadcrumbs)
│   ├── graphStore.ts           (KEEP - enhance)
│   └── filterStore.ts          (KEEP)
└── utils/
    ├── distanceCalculator.ts   (NEW - hop counting)
    └── pathFinder.ts           (NEW - shortest paths)
```

### API Endpoints Needed
```typescript
// Already have:
GET /api/graph/query/callers?symbol=X
GET /api/graph/query/callees?symbol=X
GET /api/graph/categories/{category}

// Might need:
GET /api/graph/path?from=X&to=Y           // Shortest path
GET /api/graph/node/{id}/context          // All connections
GET /api/graph/node/{id}/distance?to=Y    // Hop count
```

## Example Component Code

### ConnectionsList.vue (Signpost View)
```vue
<template>
  <div class="connections-list space-y-6">
    <!-- Current Node -->
    <div class="current-node card bg-base-100 shadow-xl">
      <div class="card-body">
        <h2 class="card-title">📍 You are here: {{ node.name }}</h2>
        <div class="stats stats-horizontal">
          <div class="stat">
            <div class="stat-title">Callers</div>
            <div class="stat-value text-blue-500">{{ callers.length }}</div>
          </div>
          <div class="stat">
            <div class="stat-title">Callees</div>
            <div class="stat-value text-green-500">{{ callees.length }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Callers (Parents) -->
    <section v-if="callers.length">
      <h3 class="text-lg font-bold mb-3">↑ CALLED BY</h3>
      <div class="space-y-2">
        <NodeTile 
          v-for="caller in callers" 
          :key="caller.id"
          :node="caller"
          :distance="caller.distance"
          direction="inbound"
          @click="navigateTo(caller)"
        />
      </div>
    </section>

    <!-- Callees (Children) -->
    <section v-if="callees.length">
      <h3 class="text-lg font-bold mb-3">↓ CALLS</h3>
      <div class="space-y-2">
        <NodeTile 
          v-for="callee in callees" 
          :key="callee.id"
          :node="callee"
          :distance="callee.distance"
          direction="outbound"
          @click="navigateTo(callee)"
        />
      </div>
    </section>
  </div>
</template>
```

### NodeTile.vue (Signpost Tile)
```vue
<template>
  <div 
    class="node-tile card bg-base-200 hover:bg-base-300 cursor-pointer transition-all"
    :class="tileClasses"
  >
    <div class="card-body p-4">
      <div class="flex items-start gap-3">
        <!-- Icon -->
        <div class="text-2xl">{{ icon }}</div>
        
        <!-- Content -->
        <div class="flex-1">
          <h4 class="font-bold">{{ node.name }}</h4>
          <p class="text-sm opacity-70">{{ node.file }}</p>
          
          <!-- Signpost Info -->
          <div class="flex gap-4 text-xs mt-2">
            <span class="badge badge-sm">
              {{ distance === 0 ? 'Same file' : `${distance} hops away` }}
            </span>
            <span class="badge badge-sm badge-outline">
              Complexity {{ node.complexity }}
            </span>
          </div>
        </div>

        <!-- Distance Indicator -->
        <div class="text-right">
          <div class="text-2xl font-bold" :class="distanceColor">
            {{ distance }}
          </div>
          <div class="text-xs opacity-70">hops</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  node: any
  distance: number
  direction: 'inbound' | 'outbound'
}>()

const icon = computed(() => {
  if (props.node.isEntryPoint) return '🚀'
  if (props.node.isHub) return '🔀'
  if (props.node.isLeaf) return '🍃'
  if (props.direction === 'inbound') return '🔵'
  return '🟢'
})

const distanceColor = computed(() => {
  if (props.distance === 0) return 'text-yellow-500'
  if (props.distance <= 2) return 'text-green-500'
  if (props.distance <= 5) return 'text-blue-500'
  return 'text-red-500'
})

const tileClasses = computed(() => ({
  'border-l-4 border-blue-500': props.direction === 'inbound',
  'border-l-4 border-green-500': props.direction === 'outbound',
}))
</script>
```

## Why This Approach Works

1. **Familiar metaphor**: Everyone understands maps and signposts
2. **Scannable**: Vertical list is easier to read than graph
3. **Actionable**: Click tile → navigate, no graph knowledge needed
4. **Progressive disclosure**: Start simple, add 3D later if wanted
5. **Fast**: No expensive graph rendering on every navigation
6. **Mobile-friendly**: Lists work on any screen size

## Next Steps

Would you like me to:
1. **Start implementing Phase 1** (simplified list view)?
2. **Prototype the NodeTile component** to show the signpost concept?
3. **Research 3D libraries** more thoroughly?
4. **Create a quick mockup** in the current codebase?

Let me know what resonates most with your vision!
