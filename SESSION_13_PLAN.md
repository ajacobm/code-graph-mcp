# Session 13: Desktop Workflow Panels & Performance Fixes

**Branch**: `feature/desktop-panels` (new)  
**Base**: `feature/sigma-graph-spike @ 4d5c8c9`  
**Priority**: P0 Performance + P1 Desktop UX

---

## 🎯 Vision: Panel-Based Desktop Workflow App

Transform the mobile-first UI into a **desktop knowledge mining tool** with resizable panels for rich code interaction.

### Panel Architecture (Desktop Layout)

```
┌────────────────────────────────────────────────────────────────────┐
│  Header: Code Graph | 🔍 Search | 🔄 Re-analyze | Stats            │
├──────────────┬──────────────────────────────┬─────────────────────┤
│              │                              │                     │
│   Navigator  │      Main Content Panel      │   Inspector Panel   │
│   (250px)    │         (flex-1)             │     (400px)         │
│              │                              │                     │
│ 📂 Browse    │  Depends on active view:     │ 📍 Selected Node    │
│ 🔗 Conns     │                              │                     │
│ 🔍 Search    │  - Browse: Category tiles    │ Name: foo()         │
│ 📊 Graph     │  - Connections: List view    │ Type: function      │
│ 🛠️ Tools     │  - Search: Results table     │ Lang: Python        │
│              │  - Graph: Force-graph viz    │ Complexity: 12      │
│              │  - Code: Syntax highlighted  │                     │
│              │                              │ ─────────────────   │
│              │                              │                     │
│              │                              │ 📖 Code Preview     │
│              │                              │                     │
│              │                              │ def foo():          │
│              │                              │   ...               │
│              │                              │                     │
│              │                              │ ─────────────────   │
│              │                              │                     │
│              │                              │ 📝 Metadata/Notes   │
│              │                              │                     │
│              │                              │ AI Summary:         │
│              │                              │ "This function..."  │
│              │                              │                     │
└──────────────┴──────────────────────────────┴─────────────────────┘
```

### Panel Responsibilities

#### **Left Navigator Panel (250px fixed)**
- **Browse Mode**: Category cards (Entry Points, Hubs, Leaves)
- **Search Mode**: Query input, filters, recent searches
- **Tools Mode**: Graph tools (find callers/callees/references)
- **Settings**: Pagination size, theme, export options

#### **Main Content Panel (flex-1, resizable)**
**Multi-view with tab/mode switching:**
1. **Grid View**: NodeTile cards (current Browse tab)
   - Pagination controls at bottom
   - Sortable by name/complexity/degree
   - Filter bar at top

2. **List View**: Data table for large result sets
   - Virtual scrolling (1000+ rows)
   - Columns: Name, Type, Language, Complexity, File, Callers, Callees
   - Click row → select node in Inspector

3. **Connections View**: Current ConnectionsList design
   - Callers section (with Load More)
   - Callees section (with Load More)
   - Siblings section

4. **Graph View**: Force-graph visualization
   - Interactive 2D/3D network
   - Zoom, pan, click to select
   - Highlight connected nodes

5. **Code View**: Syntax-highlighted source code
   - Show selected node's file
   - Jump to line number
   - Inline annotations for relationships

#### **Right Inspector Panel (400px, resizable, collapsible)**
**Three sections (vertically stacked, scrollable):**

1. **📍 Selected Node Details** (always visible when node selected)
   - Name, type, language, complexity
   - File path and line number
   - Metadata badges (is_entry_point, is_hub, etc.)
   - Quick actions: "View Code", "Find Callers", "Copy ID"

2. **📖 Code Preview** (syntax-highlighted)
   - First 20 lines of node's definition
   - "View Full File" button
   - Collapsible section header

3. **📝 Metadata & AI Notes** (future feature)
   - Auto-generated summary (LLM-powered)
   - User annotations/bookmarks
   - Related documentation links
   - Code smell warnings
   - Quality metrics

---

## 🚨 P0: Critical Performance Fixes (Do First!)

### 1. Backend Pagination
**Files**: `src/code_graph_mcp/server/graph_api.py`

Add `limit` and `offset` parameters to query endpoints:

```python
@router.get("/query/callers")
async def find_callers(
    symbol: str,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    # ... existing logic ...
    callers = await engine.find_function_callers(symbol)
    total = len(callers)
    paginated = callers[offset:offset + limit]
    
    return {
        "symbol": symbol,
        "total_callers": total,
        "callers": paginated,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total
    }
```

Apply same pattern to:
- `/query/callees`
- `/query/references`
- `/categories/{category}` (already has pagination ✅)

### 2. Frontend Load More Pattern
**Files**: `frontend/src/components/ConnectionsList.vue`

Replace full list rendering with progressive loading:

```typescript
const displayedCallers = ref<any[]>([])
const totalCallers = ref(0)
const currentOffset = ref(0)
const pageSize = 50

async function loadMoreCallers() {
  const result = await graphClient.findCallers(symbol, pageSize, currentOffset.value)
  displayedCallers.value.push(...result.callers)
  totalCallers.value = result.total_callers
  currentOffset.value += pageSize
}

// Template
<div v-if="hasMoreCallers">
  <button @click="loadMoreCallers">
    Load More ({totalCallers - displayedCallers.length} remaining)
  </button>
</div>
```

### 3. Import Node Filtering
**Files**: `src/code_graph_mcp/server/graph_api.py` (categories endpoint)

Filter out common stdlib imports from Entry Points:

```python
STDLIB_IMPORTS = {
    'python': {'re', 'os', 'sys', 'json', 'asyncio', 'logging', 'time', 'pathlib'},
    'javascript': {'react', 'vue', 'fs', 'path'},
    'typescript': {'react', 'vue', '@types/*'}
}

def is_stdlib_import(node):
    if node.node_type == NodeType.IMPORT:
        return node.name.lower() in STDLIB_IMPORTS.get(node.language.lower(), set())
    return False

# In get_nodes_by_category
if category == 'entry_points':
    entry_nodes = [n for n in all_nodes if in_degree == 0 and not is_stdlib_import(n)]
```

### 4. Fix Horizontal Scroll
**Files**: `frontend/src/App.vue`

Change grid layout max-width:

```vue
<!-- Current -->
<main class="max-w-7xl mx-auto px-4 py-8">

<!-- Fixed -->
<main class="w-full px-4 py-8">
  <div class="max-w-full mx-auto">
```

---

## 🎨 P1: Desktop Panel System Implementation

### Phase 1: Three-Panel Layout
**Files**: `frontend/src/App.vue`, `frontend/src/components/NavigatorPanel.vue`, `frontend/src/components/InspectorPanel.vue`

**New Structure**:
```vue
<template>
  <div class="app-container h-screen flex flex-col">
    <!-- Header -->
    <AppHeader />
    
    <!-- Main: Three-column layout -->
    <div class="flex-1 flex overflow-hidden">
      <!-- Left Navigator (fixed 250px) -->
      <NavigatorPanel class="w-64 border-r border-slate-700" />
      
      <!-- Center Main Content (flex) -->
      <MainContentPanel class="flex-1 overflow-auto" />
      
      <!-- Right Inspector (resizable 400px, collapsible) -->
      <InspectorPanel 
        class="w-96 border-l border-slate-700"
        :collapsible="true"
        :resizable="true"
      />
    </div>
  </div>
</template>
```

### Phase 2: Navigator Panel Component
**File**: `frontend/src/components/NavigatorPanel.vue` (NEW)

**Features**:
- Mode selector (Browse, Search, Tools, Settings)
- Collapsible sections
- Recent selections history
- Saved searches list

**Implementation**:
```vue
<template>
  <div class="navigator-panel bg-slate-900 flex flex-col">
    <!-- Mode Tabs -->
    <div class="tabs tabs-boxed">
      <button @click="mode = 'browse'" :class="{ 'tab-active': mode === 'browse' }">
        📂 Browse
      </button>
      <button @click="mode = 'search'" :class="{ 'tab-active': mode === 'search' }">
        🔍 Search
      </button>
      <button @click="mode = 'tools'" :class="{ 'tab-active': mode === 'tools' }">
        🛠️ Tools
      </button>
    </div>
    
    <!-- Mode Content -->
    <div class="flex-1 overflow-auto p-4">
      <BrowseMode v-if="mode === 'browse'" />
      <SearchMode v-else-if="mode === 'search'" />
      <ToolsMode v-else-if="mode === 'tools'" />
    </div>
  </div>
</template>
```

### Phase 3: Inspector Panel with Code Preview
**File**: `frontend/src/components/InspectorPanel.vue` (NEW)

**Three Sections**:
1. **Node Details** (current details pane, enhanced)
2. **Code Preview** (NEW - syntax highlighted)
3. **Metadata/Notes** (NEW - for future AI integration)

**Code Preview Implementation**:
```vue
<template>
  <div class="inspector-panel">
    <!-- Section 1: Node Details -->
    <section class="node-details">
      <h3>📍 Selected Node</h3>
      <!-- Existing details pane content -->
    </section>
    
    <!-- Section 2: Code Preview -->
    <section v-if="selectedNode" class="code-preview">
      <div class="section-header" @click="toggleCodePreview">
        <h3>📖 Code Preview</h3>
        <button>{{ codeExpanded ? '▼' : '▶' }}</button>
      </div>
      
      <div v-show="codeExpanded" class="code-container">
        <pre><code class="language-python" v-html="highlightedCode"></code></pre>
        <button @click="viewFullFile">View Full File</button>
      </div>
    </section>
    
    <!-- Section 3: Metadata & Notes (Future) -->
    <section class="metadata-notes">
      <div class="section-header">
        <h3>📝 Metadata & Notes</h3>
      </div>
      
      <div class="placeholder">
        <p class="text-slate-500 text-sm">AI-generated summaries coming soon...</p>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useGraphStore } from '../stores/graphStore'
// Use highlight.js or shiki for syntax highlighting
import hljs from 'highlight.js'

const graphStore = useGraphStore()
const codeExpanded = ref(true)
const codeSnippet = ref('')

const highlightedCode = computed(() => {
  if (!codeSnippet.value) return ''
  return hljs.highlightAuto(codeSnippet.value).value
})

watch(() => graphStore.selectedNode, async (node) => {
  if (node?.location?.file_path) {
    // Fetch code snippet from backend
    const result = await fetch(`/api/graph/code-snippet?file=${node.location.file_path}&line=${node.location.start_line}`)
    codeSnippet.value = await result.text()
  }
})
</script>
```

### Phase 4: Main Content Panel Views
**File**: `frontend/src/components/MainContentPanel.vue` (NEW)

**View Modes**:
- Grid View (existing NodeTile grid)
- Table View (NEW - for large datasets)
- Connections View (existing ConnectionsList)
- Graph View (force-graph)
- Code View (full file viewer)

**View Switcher**:
```vue
<div class="view-switcher">
  <button @click="view = 'grid'">⊞ Grid</button>
  <button @click="view = 'table'">⊟ Table</button>
  <button @click="view = 'connections'">🔗 Connections</button>
  <button @click="view = 'graph'">🌐 Graph</button>
  <button @click="view = 'code'">📄 Code</button>
</div>

<component :is="currentViewComponent" />
```

---

## 🛠️ Implementation Plan

### Step 1: Backend Pagination (30 min)
1. Modify `graph_api.py` - Add limit/offset to 3 query endpoints
2. Update response models to include pagination metadata
3. Test with `re` node (should return 50 of 1,123)

### Step 2: Frontend Load More (45 min)
1. Update `graphClient.ts` - Add pagination params to API calls
2. Modify `ConnectionsList.vue` - Implement progressive loading
3. Add "Load More" button with remaining count
4. Test scrolling through 1,000+ callers

### Step 3: Layout Fixes (20 min)
1. Fix horizontal scroll in `App.vue`
2. Remove mobile-first max-width constraints
3. Test on desktop resolution (1920x1080)

### Step 4: Import Filtering (30 min)
1. Define stdlib import lists per language
2. Add `is_stdlib_import()` helper function
3. Filter from Entry Points category
4. Add separate "Library Imports" category (optional)

### Step 5: Panel System Foundation (2 hours)
1. Create `NavigatorPanel.vue` with mode tabs
2. Create `InspectorPanel.vue` with three sections
3. Create `MainContentPanel.vue` with view switching
4. Refactor `App.vue` to use three-panel layout
5. Add panel resize logic (vue-resizable or custom)

### Step 6: Code Preview Feature (1 hour)
1. Add `/api/graph/code-snippet` endpoint (backend)
   - Params: `file_path`, `line_number`, `context_lines=10`
   - Returns: Code snippet with line numbers
2. Integrate highlight.js or shiki for syntax highlighting
3. Wire up to InspectorPanel
4. Add "View Full File" button (opens Code View in main panel)

### Step 7: Search Panel (1 hour)
1. Create `SearchPanel.vue` component
2. Add search input with filters (language, type, complexity range)
3. Display results in Main Content Panel (table or grid)
4. Save recent searches to localStorage

---

## 🎨 UI/UX Improvements

### Keyboard Shortcuts
- `Ctrl+K` - Open search
- `Arrow Keys` - Navigate lists
- `Enter` - Select node
- `Esc` - Clear selection
- `Ctrl+[` / `Ctrl+]` - Navigate history back/forward

### Responsive Behavior
- **Desktop (>1280px)**: Three-panel layout
- **Tablet (768-1280px)**: Two panels (Navigator + Main, Inspector collapsible)
- **Mobile (<768px)**: Single panel with bottom tabs (current design)

### Visual Hierarchy
- **Header**: Dark gradient, sticky top
- **Navigator**: Darkest background (slate-900)
- **Main Content**: Medium background (slate-800)
- **Inspector**: Lighter background (slate-700) to stand out
- **Code Preview**: Monospace font, dark theme (VS Code style)

---

## 📦 New Components to Create

### Session 13 Components
1. `NavigatorPanel.vue` (~200 lines)
   - Mode tabs, collapsible sections
   
2. `InspectorPanel.vue` (~300 lines)
   - Node details, code preview, metadata sections
   - Resizable and collapsible
   
3. `MainContentPanel.vue` (~150 lines)
   - View switcher, component renderer
   
4. `TableView.vue` (~250 lines)
   - Virtual scrolling data table
   - Sortable columns, row selection
   
5. `SearchPanel.vue` (~200 lines)
   - Search input, filters, recent searches
   
6. `CodePreview.vue` (~150 lines)
   - Syntax highlighting, line numbers
   - Jump to definition links

### Session 13 Utilities
1. `useKeyboardNav.ts` composable
2. `useResizablePanel.ts` composable
3. `syntaxHighlighter.ts` helper

---

## 🔧 Backend Enhancements

### New Endpoints
1. `GET /api/graph/code-snippet`
   - Params: `file_path`, `start_line`, `end_line`, `context_lines=10`
   - Returns: `{ code: string, line_numbers: number[], language: string }`

2. `GET /api/graph/search` (enhanced)
   - Current search is basic substring
   - Add: regex support, multi-field search, score ranking
   - Pagination built-in

3. `POST /api/graph/batch-nodes`
   - Accept array of node IDs
   - Return details for all (for table view)
   - More efficient than N individual requests

---

## 📊 Dependencies to Add

### Frontend
```bash
npm install highlight.js          # Syntax highlighting
npm install @vueuse/core          # Composables (keyboard, resize)
npm install vue-virtual-scroller  # Virtual scrolling for large lists
```

### Backend
```python
# Already have all needed dependencies
# pygments (for syntax highlighting - already installed)
```

---

## 🧪 Testing Strategy

### Unit Tests
- [ ] Pagination logic in query endpoints
- [ ] Import filtering logic
- [ ] Code snippet extraction

### Integration Tests
- [ ] Load 1,000+ callers with pagination
- [ ] Panel resize and collapse interactions
- [ ] Keyboard navigation flow

### Performance Tests
- [ ] Render 10,000 node table with virtual scrolling
- [ ] Load time for code preview (target <100ms)
- [ ] Memory usage with large graphs

### UX Tests (Playwright)
- [ ] Complete workflow: Browse → Select → View Code → Search → Navigate
- [ ] Panel resize maintains state
- [ ] Keyboard shortcuts work in all views

---

## 📈 Success Criteria

### Performance
- ✅ Handle nodes with 10,000+ connections without lag
- ✅ Code preview loads in <100ms
- ✅ Virtual scrolling supports 100,000+ rows
- ✅ No horizontal scroll on desktop (1920x1080+)

### Usability
- ✅ Desktop-optimized layout with multi-column panels
- ✅ Code preview on every node selection
- ✅ Search with filters across all nodes
- ✅ Keyboard navigation throughout
- ✅ Clear visual hierarchy (know where you are)

### Developer Experience
- ✅ Clean codebase with reusable panel components
- ✅ Comprehensive documentation (this file!)
- ✅ All tests passing (80+ tests)

---

## 🗂️ File Cleanup (This Session)

### Archived to docs/archive/
- All SESSION_*_COMPLETION.md files
- All ROADMAP_*.md files
- Duplicate UI/UX planning docs
- Old final status documents

### New Root Structure
```
/
├── README.md           # Project overview
├── CRUSH.md           # Session memory (commands, notes)
├── PLANNING.md        # This file - forward-looking
├── CURRENT_STATE.md   # Rolling state tracker (updated)
├── CHANGELOG.md       # Release notes
├── GETTING_STARTED.md # Quick start guide
└── docs/
    ├── archive/       # Historical docs (18 files moved)
    └── sessions/      # Detailed session logs
```

---

## 🚀 Session 13 Timeline

**Estimated**: 6-7 hours total

| Task | Time | Priority |
|------|------|----------|
| Backend pagination | 30m | P0 |
| Frontend Load More | 45m | P0 |
| Horizontal scroll fix | 20m | P0 |
| Import filtering | 30m | P0 |
| **P0 Subtotal** | **~2h** | **BLOCKING** |
| NavigatorPanel | 1h | P1 |
| InspectorPanel | 1.5h | P1 |
| MainContentPanel | 45m | P1 |
| Code Preview | 1h | P1 |
| TableView | 1h | P1 |
| Testing & Polish | 1h | P1 |
| **P1 Subtotal** | **~6h** | **HIGH** |

**Recommendation**: Complete all P0 tasks in Session 13, then evaluate time remaining for P1 panel work.

---

## 💡 Future Enhancements (Post-Session 13)

### LLM Integration
- Auto-generate function summaries with Claude
- Answer questions: "What does this function do?"
- Suggest refactoring based on graph patterns
- Find business logic in boilerplate

### Observability Features
- Real-time node highlighting during analysis
- Replay analysis sessions with timeline
- Watch mode for live code changes
- Performance profiling overlay

### Collaboration Features
- Share subgraph URLs
- Export to PDF/PNG with annotations
- Team annotations on nodes
- Code review mode with graph context

---

## 📚 Reference Links

- **Force-Graph Library**: https://github.com/vasturiano/force-graph
- **Highlight.js**: https://highlightjs.org/
- **VueUse**: https://vueuse.org/
- **DaisyUI Panels**: https://daisyui.com/components/
- **Vue Virtual Scroller**: https://github.com/Akryum/vue-virtual-scroller

---

**Status**: Ready to implement! 🚀
