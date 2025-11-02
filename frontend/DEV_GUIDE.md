# Frontend Development Guide

## Quick Start

```bash
cd frontend
npm install          # Install dependencies (do this once)
npm run dev          # Start dev server on localhost:5173
npm run build        # Build for production
npm run preview      # Preview production build locally
npm run type-check   # Run TypeScript type checker
```

## What's Running

When you run `npm run dev`:
1. Vite dev server starts on `http://localhost:5173`
2. Auto-reload on file save (HMR - Hot Module Replacement)
3. Proxies `/api/*` requests to `http://localhost:8000` (backend)
4. TypeScript compiled on the fly

## Project Structure

```
frontend/
├── src/
│   ├── main.ts              # App entry point
│   ├── App.vue              # Root component
│   ├── api/
│   │   └── graphClient.ts   # Axios API wrapper
│   ├── components/
│   │   ├── GraphViewer.vue        # Cytoscape graph
│   │   ├── NodeDetails.vue        # Right sidebar
│   │   ├── SearchBar.vue          # Top search
│   │   ├── FilterPanel.vue        # Left sidebar
│   │   └── CallChainTracer.vue    # Step-through nav
│   ├── stores/
│   │   ├── graphStore.ts    # Pinia store (graph state)
│   │   └── filterStore.ts   # Pinia store (filters)
│   ├── types/
│   │   └── graph.ts         # TypeScript interfaces
│   └── style.css            # Tailwind global styles
├── index.html               # HTML entry point
├── vite.config.ts           # Vite configuration
├── tsconfig.json            # TypeScript config
└── package.json             # Dependencies
```

## Key Technologies

**Vite**: Ultra-fast build tool and dev server
- Way faster than Webpack/Create React App
- Instant HMR (changes appear instantly)
- Near-native ES modules in dev

**Vue 3**: Modern frontend framework
- Composition API (like React hooks)
- Reactive data binding
- Single-file components (.vue files)

**Pinia**: State management (like Redux)
- Global stores for graph data
- Simpler than Vuex
- Used by `useGraphStore()` and `useFilterStore()`

**Cytoscape.js**: Graph visualization library
- Renders nodes/edges
- Dagre layout plugin for hierarchical graphs
- Click/hover/pan interactions

**Tailwind CSS**: Utility-first CSS
- Pre-built classes like `bg-gray-900`, `text-white`
- Dark theme in `tailwind.config.ts`
- No CSS files to write, just add classes to HTML

## Common Tasks

### Add a new component
```bash
# Create src/components/MyComponent.vue with:
<script setup lang="ts">
// TypeScript here
</script>

<template>
  <!-- HTML here -->
</template>

<style scoped>
/* Optional: component styles */
</style>
```

### Make an API call
```typescript
import { graphClient } from '@/api/graphClient'

const stats = await graphClient.getStats()
const nodes = await graphClient.searchNodes('foo')
```

### Use reactive state (Pinia)
```typescript
import { useGraphStore } from '@/stores/graphStore'

const store = useGraphStore()
store.traverse('node-id', 5)
console.log(store.selectedNode)
```

### Use a computed value
```typescript
import { computed } from 'vue'

const upperName = computed(() => 
  graphStore.selectedNode?.name.toUpperCase()
)
```

### Conditional rendering
```vue
<div v-if="isLoading">Loading...</div>
<div v-else-if="error">Error: {{ error }}</div>
<div v-else>Success!</div>
```

### List rendering
```vue
<button
  v-for="node in nodes"
  :key="node.id"
  @click="selectNode(node.id)"
>
  {{ node.name }}
</button>
```

## Running Backend + Frontend Together

**Terminal 1 (Backend):**
```bash
cd /home/adam/GitHub/code-graph-mcp
docker-compose -f docker-compose-multi.yml up
# Or if you have Python locally:
python -m code_graph_mcp.http_server --host 0.0.0.0 --port 8000
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm run dev
```

Then open `http://localhost:5173` in your browser.

## Debugging

**Browser DevTools** (press F12):
- Network tab: See API calls to `/api/graph/*`
- Console: See JavaScript errors and logs
- Vue DevTools: Inspect components and stores (install extension)

**VS Code**:
- Set breakpoints in `.vue` files
- Debug with VS Code debugger

## TypeScript Basics

```typescript
// Type annotations (optional but recommended)
const name: string = "foo"
const count: number = 42
const items: string[] = ["a", "b"]
const result: boolean = true

// Function types
async function getNodes(id: string): Promise<Node[]> {
  return []
}

// Interfaces
interface Node {
  id: string
  name: string
  language: string
}

// Union types
type ViewMode = 'full' | 'call_chain' | 'seams_only'
```

## Troubleshooting

**"Cannot find module"**
- Run `npm install` to get dependencies
- Check import path spelling

**"Port 5173 in use"**
- Vite uses different port if 5173 taken
- Look for "Local: http://localhost:XXXX" in terminal

**API calls fail**
- Make sure backend is running on localhost:8000
- Check `/api/*` proxy in `vite.config.ts`
- Open DevTools Network tab to see actual requests

**HMR not working**
- Restart `npm run dev`
- Hard refresh browser (Ctrl+Shift+R)

**TypeScript errors**
- They won't stop dev server, just show warnings
- Run `npm run type-check` to see all errors
- Fix by adding types or `: any` if stuck

## Next: Testing Locally

1. Start backend: `docker-compose up` or `python -m code_graph_mcp.http_server`
2. Start frontend: `npm run dev`
3. Open browser to `http://localhost:5173`
4. Try typing a node ID and clicking "Traverse"
5. Click a node in the graph to see details panel
