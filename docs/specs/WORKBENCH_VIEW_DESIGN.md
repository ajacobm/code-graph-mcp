# Workbench View Design Documentation

**Version**: 1.0  
**Date**: December 2025  
**Status**: Design Phase

---

## Executive Summary

This document outlines the design for a new workbench view that will replace the current force-directed graph visualization. The new view introduces a **sliding panel with node cards** interface that supports hierarchical drill-down navigation while maintaining the established interaction patterns like double-click navigation and breadcrumb navigation.

---

## 1. Vision and Goals

### 1.1 Primary Goals

1. **Hierarchical Navigation**: Enable intuitive drill-down from high-level modules to detailed methods
   - Python: `module → class → method`
   - .NET: `project → class → method`
   - JavaScript/TypeScript: `module → class/function`

2. **Simplified Interaction**: Replace complex force-graph manipulation with card-based navigation

3. **Maintained Workflow**: Preserve existing double-click drill-down and breadcrumb navigation patterns

4. **Testability**: Design components for unit and integration testing with Playwright

### 1.2 Secondary Goals

- Improve panel resize behavior on window resize
- Fix non-functional controls (e.g., "View Connections" button)
- Better integration of entry points, hubs, and leaves categories

---

## 2. Architecture Overview

### 2.1 Current State

```
┌─────────────────────────────────────────────────────────────────────┐
│  Header Bar                                                          │
├───────────────┬───────────────────────────────────────┬─────────────┤
│               │                                       │             │
│  ToolsPanel   │      Force-Directed Graph Canvas      │  Details    │
│  (w-64)       │      (flex-1)                         │   Panel     │
│               │                                       │  (w-80)     │
│  [Search]     │         ┌───┐                        │             │
│  [Categories] │        /│ A │\                       │  Node info  │
│  [Filters]    │       / └───┘ \                      │  Actions    │
│  [Legend]     │  ┌───┐         ┌───┐                 │             │
│               │  │ B │─────────│ C │                 │             │
│               │  └───┘         └───┘                 │             │
├───────────────┴───────────────────────────────────────┴─────────────┤
│  Status Bar                                                          │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Proposed State: Workbench View

```
┌─────────────────────────────────────────────────────────────────────┐
│  Header Bar                                                          │
│  [← Back] Breadcrumbs: src/codenav > graph_api > GraphAPIServer     │
├───────────────┬───────────────────────────────────────┬─────────────┤
│               │                                       │             │
│  Navigator    │      Workbench Canvas                 │  Details    │
│  Panel        │                                       │   Panel     │
│  (w-64)       │  ┌─────────────────────────────────┐ │  (w-80)     │
│               │  │ 📦 GraphAPIServer               │ │             │
│  [Search]     │  │   Complexity: 45 | Python       │ │  Selected   │
│  [Browse]     │  │                                 │ │  Node Info  │
│  [Filters]    │  └─────────────────────────────────┘ │             │
│               │                                       │  [Actions]  │
│  Categories:  │  Children (8 methods):               │             │
│  🚀 Entry     │  ┌─────────┐ ┌─────────┐ ┌─────────┐ │  Connections│
│  🔀 Hubs      │  │ startup │ │ get_node│ │ search  │ │  list here  │
│  🍃 Leaves    │  └─────────┘ └─────────┘ └─────────┘ │             │
│               │  ┌─────────┐ ┌─────────┐ ┌─────────┐ │             │
│               │  │ traverse│ │ call_ch │ │ export  │ │             │
│               │  └─────────┘ └─────────┘ └─────────┘ │             │
├───────────────┴───────────────────────────────────────┴─────────────┤
│  Status Bar: Nodes: 974 | Edges: 12,767 | WS: ● | Level: 2/3       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Component Design

### 3.1 WorkbenchCanvas Component

The central component replacing ForceGraph, displaying the current root node and its children as interactive cards.

```typescript
interface WorkbenchCanvasProps {
  // Current focused node (root of the current view)
  rootNode: GraphNode | null
  
  // Children of the root node
  childNodes: GraphNode[]
  
  // Navigation state
  navigationStack: NavigationEntry[]
  
  // Interaction handlers
  onNodeClick: (node: GraphNode) => void
  onNodeDoubleClick: (node: GraphNode) => void  // Drill down
  onBackClick: () => void
  
  // Display options
  viewMode: 'grid' | 'list'
  sortBy: 'name' | 'complexity' | 'type'
  filterBy: string[]
}
```

#### Visual Design

**Root Node Card (Hero)**:
```
┌───────────────────────────────────────────────────────────────┐
│  📦 GraphAPIServer                              [Type: class] │
│  ─────────────────────────────────────────────────────────────│
│  📍 src/codenav/server/graph_api.py:45                        │
│  📊 Complexity: 45  |  📏 Lines: 234  |  🐍 Python            │
│                                                               │
│  8 methods  |  3 callers  |  12 callees                       │
└───────────────────────────────────────────────────────────────┘
```

**Child Node Cards (Grid)**:
```
┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│ ⚙️ startup          │  │ ⚙️ get_node         │  │ ⚙️ search_nodes     │
│ Complexity: 8       │  │ Complexity: 5       │  │ Complexity: 12      │
│ Lines: 45           │  │ Lines: 23           │  │ Lines: 67           │
│ [Double-click ▶]   │  │ [Double-click ▶]   │  │ [Double-click ▶]   │
└─────────────────────┘  └─────────────────────┘  └─────────────────────┘
```

### 3.2 BreadcrumbNavigation Component

Provides context-aware navigation back through the hierarchy.

```typescript
interface BreadcrumbNavigationProps {
  // Full path from root
  path: NavigationEntry[]
  
  // Navigate to specific level
  onNavigateTo: (index: number) => void
  
  // Quick home button
  onHome: () => void
}
```

**Visual Design**:
```
← [Home] / src/codenav / server / graph_api.py / GraphAPIServer / startup()
          ↑ clickable    ↑ clickable   ↑ clickable    ↑ current (bold)
```

### 3.3 NodeCard Component

Reusable card for displaying node information.

```typescript
interface NodeCardProps {
  node: GraphNode
  variant: 'hero' | 'grid' | 'list'
  isSelected: boolean
  isHighlighted: boolean
  
  // Interaction
  onClick: () => void
  onDoubleClick: () => void
  
  // Display
  showMetrics: boolean
  showConnections: boolean
}
```

**Variants**:

1. **Hero** (root node): Large, detailed, centered
2. **Grid** (children): Medium cards in grid layout
3. **List** (alternative view): Compact rows with essential info

### 3.4 Updated ToolsPanel

Enhance existing panel with workbench-specific features:

```typescript
interface ToolsPanelProps {
  // Existing
  isCollapsed: boolean
  onToggleCollapse: () => void
  onSearch: (query: string) => void
  
  // New: Category navigation
  categories: CategoryStats[]
  onCategorySelect: (category: 'entry_points' | 'hubs' | 'leaves') => void
  
  // New: View controls
  viewMode: 'grid' | 'list'
  onViewModeChange: (mode: 'grid' | 'list') => void
  
  // New: Sort/filter
  sortBy: string
  onSortChange: (sort: string) => void
}
```

### 3.5 Updated DetailsPanel

Fix existing issues and add connection list:

```typescript
interface DetailsPanelProps {
  // Existing
  isCollapsed: boolean
  onToggleCollapse: () => void
  
  // New: Connection list (replaces broken View Connections button)
  connections: {
    callers: GraphNode[]
    callees: GraphNode[]
    siblings: GraphNode[]
  }
  
  // Navigation
  onNavigateToNode: (nodeId: string) => void
  onCenterNode: (nodeId: string) => void
}
```

---

## 4. Navigation Flow

### 4.1 High-Level Drill-Down Workflow

**Python Example**:
```
Level 0: All Modules
    ├── src/codenav/parser/
    ├── src/codenav/server/
    └── src/codenav/tools/
         ↓ Double-click "server"

Level 1: src/codenav/server (Module Contents)
    ├── graph_api.py
    ├── http_server.py
    └── websocket_server.py
         ↓ Double-click "graph_api.py"

Level 2: graph_api.py (Classes)
    ├── GraphAPIServer (class)
    └── GraphAPIRouter (class)
         ↓ Double-click "GraphAPIServer"

Level 3: GraphAPIServer (Methods)
    ├── __init__()
    ├── startup()
    ├── get_node()
    └── search_nodes()
```

**.NET Example**:
```
Level 0: Projects/Assemblies
    ├── MyApp.Web
    ├── MyApp.Core
    └── MyApp.Data
         ↓ Double-click "MyApp.Core"

Level 1: Namespaces
    ├── MyApp.Core.Services
    └── MyApp.Core.Models
         ↓ Double-click "Services"

Level 2: Classes
    ├── UserService
    └── OrderService
         ↓ Double-click "UserService"

Level 3: Methods
    ├── GetUser()
    ├── CreateUser()
    └── UpdateUser()
```

### 4.2 Navigation Actions

| Action | Behavior |
|--------|----------|
| Single-click on child | Select node, show details in right panel |
| Double-click on child | Drill into node (becomes new root) |
| Click breadcrumb | Navigate to that level |
| Click ← Back | Navigate to parent level |
| Click Home | Return to top-level (all modules) |
| Ctrl+Click | Multi-select for comparison (future) |

### 4.3 Navigation Stack Management

```typescript
// graphStore.ts additions
interface NavigationState {
  // Current focus
  rootNodeId: string | null
  
  // Breadcrumb path
  navigationStack: NavigationEntry[]
  
  // Cached data per level
  levelCache: Map<string, GraphData>
}

// Actions
drillIntoNode: (nodeId: string) => Promise<void>
navigateBack: () => void
navigateToLevel: (index: number) => void
resetToRoot: () => void
```

---

## 5. Entry Points, Hubs, and Leaves Integration

### 5.1 Category Tiles in Navigator Panel

Instead of abstract categories, present them as **quick filters**:

```
┌─────────────────────────────────┐
│  📋 Quick Access                │
├─────────────────────────────────┤
│  🚀 Entry Points (24)           │  ← Functions with no callers
│     Entry functions, API routes │
├─────────────────────────────────┤
│  🔀 Hubs (12)                   │  ← Highly connected nodes
│     Central utilities, core     │
├─────────────────────────────────┤
│  🍃 Leaves (156)                │  ← Functions with no callees
│     Utility functions, helpers  │
└─────────────────────────────────┘
```

### 5.2 Category View Behavior

When a category is selected:

1. **Entry Points view**: Show all entry point nodes as root cards (no parent context)
2. **Hubs view**: Show highly-connected nodes with connection counts
3. **Leaves view**: Show leaf nodes grouped by module

Each card in these views supports the same double-click drill-down.

### 5.3 Category Badges on Node Cards

Show category badges on node cards when relevant:

```
┌─────────────────────┐
│ ⚙️ main            │
│ 🚀 Entry Point     │  ← Badge
│ Complexity: 3       │
│ Lines: 15           │
└─────────────────────┘
```

---

## 6. Resize and Layout Fixes

### 6.1 Current Issues

1. **Main panel doesn't resize correctly on window resize**
2. **Right side panel sometimes disappears**
3. **View Connections button non-functional**

### 6.2 Solutions

#### Panel Resize Fix

```typescript
// Current: Fixed widths with flex-1 center
// Problem: No min-width constraints, ResizeObserver not always firing

// Solution: CSS Grid with minmax constraints
.layout-container {
  display: grid;
  grid-template-columns: 
    minmax(200px, 16rem)    /* Left panel: min 200px, prefer 256px */
    minmax(400px, 1fr)       /* Center: min 400px, takes remaining */
    minmax(200px, 20rem);    /* Right panel: min 200px, prefer 320px */
  height: 100%;
}

// Fallback for very small screens
@media (max-width: 768px) {
  .layout-container {
    grid-template-columns: 1fr;
  }
}
```

#### ResizeObserver Enhancement

```typescript
// Enhanced resize handling in ForceGraph/WorkbenchCanvas
useEffect(() => {
  if (!containerRef.current) return

  const container = containerRef.current
  
  const handleResize = () => {
    const { width, height } = container.getBoundingClientRect()
    if (width > 0 && height > 0) {
      // Update canvas dimensions
      setDimensions({ width, height })
    }
  }

  // Initial size
  handleResize()
  
  // Observe changes
  const resizeObserver = new ResizeObserver(handleResize)
  resizeObserver.observe(container)
  
  // Also listen to window resize as fallback
  window.addEventListener('resize', handleResize)
  
  return () => {
    resizeObserver.disconnect()
    window.removeEventListener('resize', handleResize)
  }
}, [])
```

#### View Connections Button Fix

```typescript
// Current: Button exists but onViewConnections prop not connected
// Solution: Implement connection list in DetailsPanel

// DetailsPanel.tsx
interface DetailsPanelProps {
  // ... existing props
  onViewConnections?: (nodeId: string) => void  // MUST be connected
}

// App.tsx - connect the handler
const handleViewConnections = useCallback((nodeId: string) => {
  // Load callers/callees for the node
  loadNodeConnections(nodeId)
  // Show connections section in details panel
  setShowConnections(true)
}, [loadNodeConnections])

<DetailsPanel 
  onViewConnections={handleViewConnections}  // Connect it!
  // ...other props
/>
```

---

## 7. Testing Strategy with Playwright

### 7.1 Testing Philosophy

Following test-driven development principles from `docs/guides/PLAYWRIGHT_TESTING_GUIDE.md`:

1. **Write tests BEFORE implementing features**
2. **Use Page Object Model for maintainability**
3. **Data-test attributes for stable selectors**

### 7.2 Component-Level Testing Structure

```
tests/
├── e2e/                          # Playwright end-to-end tests
│   ├── conftest.py              # Pytest fixtures
│   ├── pages/                   # Page Object Models
│   │   ├── workbench_canvas.py
│   │   ├── navigator_panel.py
│   │   ├── details_panel.py
│   │   └── breadcrumb_nav.py
│   ├── test_workbench_navigation.py
│   ├── test_node_cards.py
│   ├── test_drill_down.py
│   ├── test_breadcrumbs.py
│   ├── test_categories.py
│   └── test_layout_resize.py
├── components/                   # Vitest component tests
│   ├── NodeCard.test.tsx
│   ├── BreadcrumbNav.test.tsx
│   └── WorkbenchCanvas.test.tsx
└── integration/                  # Backend integration tests
```

### 7.3 Example Test Cases

#### Drill-Down Navigation Test
```python
# tests/e2e/test_drill_down.py
def test_double_click_drills_into_node(app_page):
    """Double-clicking a node navigates into its children."""
    # Arrange - Start at module level
    app_page.wait_for_selector('[data-test="workbench-canvas"]')
    initial_breadcrumb_count = app_page.locator('[data-test="breadcrumb-item"]').count()
    
    # Act - Double-click a module node
    app_page.locator('[data-test="node-card"][data-node-type="module"]').first.dblclick()
    
    # Assert - Breadcrumb added, children displayed
    new_breadcrumb_count = app_page.locator('[data-test="breadcrumb-item"]').count()
    assert new_breadcrumb_count == initial_breadcrumb_count + 1
    
    # Children are now displayed
    expect(app_page.locator('[data-test="node-card"]')).to_have_count_greater_than(0)

def test_breadcrumb_navigation_goes_to_level(app_page):
    """Clicking a breadcrumb navigates to that level."""
    # Arrange - Drill down 2 levels
    app_page.locator('[data-test="node-card"]').first.dblclick()
    app_page.locator('[data-test="node-card"]').first.dblclick()
    
    # Act - Click the first breadcrumb
    app_page.locator('[data-test="breadcrumb-item"]').first.click()
    
    # Assert - Back at root level
    breadcrumb_count = app_page.locator('[data-test="breadcrumb-item"]').count()
    assert breadcrumb_count == 1
```

#### Layout Resize Test
```python
# tests/e2e/test_layout_resize.py
def test_panels_maintain_proportions_on_resize(app_page):
    """Panel widths adjust proportionally when window resizes."""
    # Arrange - Get initial widths
    app_page.set_viewport_size({'width': 1920, 'height': 1080})
    initial_center_width = app_page.locator('[data-test="workbench-canvas"]').bounding_box()['width']
    
    # Act - Resize window
    app_page.set_viewport_size({'width': 1280, 'height': 800})
    
    # Assert - Center panel shrinks proportionally
    new_center_width = app_page.locator('[data-test="workbench-canvas"]').bounding_box()['width']
    assert new_center_width < initial_center_width
    assert new_center_width > 400  # Minimum width maintained

def test_right_panel_stays_visible_on_resize(app_page):
    """Right details panel remains visible after window resize."""
    # Arrange
    app_page.set_viewport_size({'width': 1920, 'height': 1080})
    expect(app_page.locator('[data-test="details-panel"]')).to_be_visible()
    
    # Act - Resize to smaller
    app_page.set_viewport_size({'width': 1024, 'height': 768})
    
    # Assert - Still visible
    expect(app_page.locator('[data-test="details-panel"]')).to_be_visible()
```

#### Category Selection Test
```python
# tests/e2e/test_categories.py
def test_entry_points_category_shows_correct_nodes(app_page):
    """Entry Points category shows only nodes with no callers."""
    # Act - Select Entry Points category
    app_page.locator('[data-test="category-entry-points"]').click()
    
    # Assert - Cards are displayed
    cards = app_page.locator('[data-test="node-card"]')
    expect(cards).to_have_count_greater_than(0)
    
    # All cards have entry point badge
    for card in cards.all():
        expect(card.locator('[data-test="badge-entry-point"]')).to_be_visible()
```

### 7.4 Data-Test Attributes Convention

```tsx
// Workbench components
<div data-test="workbench-canvas">
  <div data-test="root-node-card" data-node-id={rootNode.id}>
  <div data-test="child-nodes-grid">
    <div data-test="node-card" data-node-id={node.id} data-node-type={node.type}>

// Breadcrumbs
<nav data-test="breadcrumb-nav">
  <button data-test="breadcrumb-home">
  <span data-test="breadcrumb-item" data-level={index}>

// Navigator panel
<aside data-test="navigator-panel">
  <button data-test="category-entry-points">
  <button data-test="category-hubs">
  <button data-test="category-leaves">

// Details panel  
<aside data-test="details-panel">
  <div data-test="node-details">
  <button data-test="view-connections-btn">
  <div data-test="connections-list">
```

---

## 8. Implementation Roadmap

### Phase 1: Foundation (Week 1)

- [ ] Create WorkbenchCanvas component
- [ ] Create NodeCard component with variants
- [ ] Create BreadcrumbNavigation component
- [ ] Add navigation stack management to graphStore
- [ ] Write Playwright tests for navigation

### Phase 2: Integration (Week 2)

- [ ] Replace ForceGraph with WorkbenchCanvas in App.tsx
- [ ] Update ToolsPanel with view mode controls
- [ ] Implement category navigation
- [ ] Fix layout resize issues
- [ ] Fix View Connections button

### Phase 3: Polish (Week 3)

- [ ] Add keyboard navigation (arrow keys, Enter, Escape)
- [ ] Add loading states and transitions
- [ ] Implement grid/list view toggle
- [ ] Add sort/filter controls
- [ ] Performance optimization for large node sets

### Phase 4: Testing (Week 4)

- [ ] Complete Playwright E2E test suite
- [ ] Add Vitest component tests
- [ ] Visual regression testing setup
- [ ] CI/CD integration

---

## 9. Known Issues to Track

The following issues should be tracked as separate bugs/features:

### Bugs

1. **Main panel resize issue**: Center canvas doesn't resize correctly on window resize
2. **Right panel disappears**: Details panel sometimes lost on resize
3. **View Connections button non-functional**: Button exists but doesn't work

### Features

1. **Keyboard navigation**: Arrow keys to navigate between cards
2. **Multi-select**: Ctrl+click to select multiple nodes for comparison
3. **Drag-and-drop**: Reorder cards (future)
4. **Export view**: Screenshot/export current view

---

## 10. Agent Documentation Note

> **For Copilot/Agent Documentation**: When implementing or modifying frontend tests, refer to this design document for:
> - Component structure and props
> - Data-test attribute naming conventions
> - Page Object Model patterns
> - Test case examples
>
> The testing strategy emphasizes **test-driven development** with Playwright for E2E tests and Vitest for component-level tests. Always write tests before implementing features.

---

## Appendix A: Type Definitions

```typescript
// New types for workbench view

export interface WorkbenchState {
  // Current root node
  rootNode: GraphNode | null
  
  // Children of root
  childNodes: GraphNode[]
  
  // Navigation history
  navigationStack: NavigationEntry[]
  
  // View settings
  viewMode: 'grid' | 'list'
  sortBy: 'name' | 'complexity' | 'type' | 'line'
  
  // Filters
  categoryFilter: 'all' | 'entry_points' | 'hubs' | 'leaves'
}

export interface NodeCardVariant {
  type: 'hero' | 'grid' | 'list'
  showMetrics: boolean
  showBadges: boolean
  showActions: boolean
}

export interface CategoryStats {
  id: 'entry_points' | 'hubs' | 'leaves'
  label: string
  icon: string
  count: number
  description: string
}
```

---

## Appendix B: API Endpoints Used

| Endpoint | Purpose | Current Status |
|----------|---------|----------------|
| `/api/graph/export` | Full graph for initial load | ✅ Exists |
| `/api/graph/subgraph` | Focused subgraph around node | ✅ Exists |
| `/api/graph/nodes/{id}` | Single node details | ✅ Exists |
| `/api/graph/categories/{cat}` | Entry points, hubs, leaves | ✅ Exists |
| `/api/graph/query/callers` | Node callers | ✅ Exists |
| `/api/graph/query/callees` | Node callees | ✅ Exists |

---

*Document created for CodeNavigator workbench view design.*
