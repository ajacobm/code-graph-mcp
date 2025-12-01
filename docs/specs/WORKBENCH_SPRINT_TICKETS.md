# Workbench View - Sprint Planning Ticket Breakdown

**Source Document**: `docs/specs/WORKBENCH_VIEW_DESIGN.md`  
**Date**: December 2025  
**Status**: Ready for Ticket Creation

---

## Overview

This document provides a complete breakdown of tickets for implementing the Workbench View feature. The tickets are organized into an Epic with Stories and Tasks, ready for creation in GitHub Issues.

## Epic Summary

| Metric | Value |
|--------|-------|
| **Epic** | Workbench View Implementation |
| **Stories** | 4 (one per phase) |
| **Tasks** | 19 total |
| **Estimated Duration** | 4 weeks |
| **Affected Areas** | Frontend (primary), API (minor) |

---

## Branching Strategy

### Recommended Branch Structure

```
main
  └── epic/workbench-view                    # Epic branch - merge when complete
        ├── story/workbench-foundation       # Phase 1 - Foundation
        │     ├── task/workbench-canvas
        │     ├── task/node-card-component
        │     ├── task/breadcrumb-navigation
        │     ├── task/navigation-stack-store
        │     └── task/navigation-playwright-tests
        │
        ├── story/workbench-integration      # Phase 2 - Integration
        │     ├── task/view-toggle-system
        │     ├── task/update-tools-panel
        │     ├── task/category-navigation
        │     ├── task/fix-layout-resize
        │     └── task/fix-view-connections
        │
        ├── story/workbench-polish           # Phase 3 - Polish
        │     ├── task/keyboard-navigation
        │     ├── task/loading-states
        │     ├── task/grid-list-toggle
        │     ├── task/sort-filter-controls
        │     └── task/performance-optimization
        │
        └── story/workbench-testing          # Phase 4 - Testing
              ├── task/playwright-e2e-suite
              ├── task/vitest-component-tests
              ├── task/visual-regression
              └── task/testing-ci-integration
```

### Merge Strategy for This Epic

1. **Task Branches**: Squash merge into story branch
2. **Story Branches**: Regular merge into epic branch after all tasks complete
3. **Epic Branch**: Merge commit into `main` when all stories are complete
4. **Hotfixes**: Cherry-pick from main to epic branch if needed during development

### When to Merge to Main

- Option A: Merge entire epic when all 4 phases complete
- Option B: Merge after Phase 2 (Integration) for early feedback, then continue
- **Recommendation**: Option B - merge after Phase 2 to get user feedback on core functionality

---

## Epic

### EPIC-001: Workbench View Implementation

**Description**:  
Implement a new card-based hierarchical navigation view (Workbench View) that coexists with the existing force-directed graph visualization. Users can toggle between views and set their preferred default. The workbench view provides intuitive drill-down from high-level modules to detailed methods.

**Business Value**:
- Improved navigation for large codebases
- Better performance (lazy-loaded graph)
- Dual view options for different use cases
- Fixes existing resize and connection bugs

**Success Criteria**:
- [ ] Users can switch between Workbench and Graph views
- [ ] Double-click drill-down works in Workbench view
- [ ] Breadcrumb navigation functional
- [ ] Category quick access works (Entry Points, Hubs, Leaves)
- [ ] Layout resize issues fixed
- [ ] View Connections button works
- [ ] 80%+ test coverage on new components
- [ ] Performance acceptable for 1000+ node graphs

**Labels**: `type: feature`, `area: frontend`, `priority: high`

---

## Story 1: Foundation (Phase 1 - Week 1)

### STORY-001: Workbench Foundation Components

**As a** developer exploring a codebase  
**I want** a card-based view showing the current node and its children  
**So that** I can navigate the code hierarchy visually

**Acceptance Criteria**:
- [ ] WorkbenchCanvas component renders current node and children
- [ ] NodeCard component displays node information with variants (hero, grid, list)
- [ ] BreadcrumbNavigation shows path and allows level jumping
- [ ] Navigation stack managed in graphStore
- [ ] Playwright tests cover drill-down navigation

**Story Points**: 8

**Labels**: `type: feature`, `area: frontend`, `priority: high`

---

### Tasks for Story 1

#### TASK-001: Create WorkbenchCanvas Component

**Description**: Create the main WorkbenchCanvas component that serves as the central view for the card-based hierarchical navigation.

**Technical Details**:
- Create `frontend/src/components/workbench/WorkbenchCanvas.tsx`
- Implement props interface per design doc (rootNode, childNodes, navigationStack, handlers)
- Display root node as hero card
- Display children in responsive grid
- Support grid/list view modes
- Add data-test attributes for Playwright

**Acceptance Criteria**:
- [ ] Component renders root node as hero card
- [ ] Component renders children in grid layout
- [ ] Responds to container resize
- [ ] Has proper TypeScript types
- [ ] Has data-test attributes per design doc

**Effort**: L

**Parent Story**: STORY-001

**Labels**: `type: feature`, `area: frontend`

---

#### TASK-002: Create NodeCard Component with Variants

**Description**: Create the reusable NodeCard component with hero, grid, and list variants for displaying node information.

**Technical Details**:
- Create `frontend/src/components/workbench/NodeCard.tsx`
- Implement three variants: hero (root), grid (children), list (compact)
- Display: name, type icon, complexity, lines, file path
- Show category badges (entry point, hub, leaf)
- Handle click and double-click events
- Add data-test attributes

**Acceptance Criteria**:
- [ ] Hero variant shows full node details
- [ ] Grid variant shows compact card layout
- [ ] List variant shows row layout
- [ ] Single-click selects, double-click drills down
- [ ] Category badges display correctly
- [ ] Responsive sizing

**Effort**: M

**Parent Story**: STORY-001

**Labels**: `type: feature`, `area: frontend`

---

#### TASK-003: Create BreadcrumbNavigation Component

**Description**: Create the breadcrumb navigation component for showing and navigating the hierarchical path.

**Technical Details**:
- Create `frontend/src/components/workbench/BreadcrumbNavigation.tsx`
- Show home button and clickable path segments
- Truncate long paths with ellipsis
- Handle navigation to any level
- Keyboard accessible
- Add data-test attributes

**Acceptance Criteria**:
- [ ] Shows clickable path segments
- [ ] Home button returns to root
- [ ] Current item is highlighted/bold
- [ ] Long paths truncate gracefully
- [ ] Keyboard navigation works

**Effort**: S

**Parent Story**: STORY-001

**Labels**: `type: feature`, `area: frontend`

---

#### TASK-004: Add Navigation Stack to GraphStore

**Description**: Extend the graphStore (Zustand) to manage navigation stack for drill-down and breadcrumb functionality.

**Technical Details**:
- Modify `frontend/src/stores/graphStore.ts`
- Add NavigationState interface per design doc
- Implement actions: drillIntoNode, navigateBack, navigateToLevel, resetToRoot
- Add level caching for performance
- Persist navigation state if needed

**Acceptance Criteria**:
- [ ] Navigation stack tracks drill-down history
- [ ] drillIntoNode pushes new level
- [ ] navigateBack pops to previous level
- [ ] navigateToLevel jumps to specific level
- [ ] resetToRoot clears stack
- [ ] State persists across component remounts

**Effort**: M

**Parent Story**: STORY-001

**Labels**: `type: feature`, `area: frontend`

---

#### TASK-005: Write Playwright Tests for Navigation

**Description**: Create Playwright E2E tests for the workbench navigation functionality following the testing guide patterns.

**Technical Details**:
- Create `tests/e2e/test_workbench_navigation.py`
- Create Page Object Models in `tests/e2e/pages/`
- Test double-click drill-down
- Test breadcrumb navigation
- Test back button
- Test home button

**Acceptance Criteria**:
- [ ] Test for double-click drill-down
- [ ] Test for breadcrumb level navigation
- [ ] Test for back button
- [ ] Test for home button
- [ ] Page Object Model used
- [ ] Tests pass in CI

**Effort**: M

**Parent Story**: STORY-001

**Labels**: `type: testing`, `area: frontend`

---

## Story 2: Integration (Phase 2 - Week 2)

### STORY-002: View Integration and Bug Fixes

**As a** user  
**I want** to toggle between Workbench and Graph views with my preference saved  
**So that** I can use whichever view suits my current task

**Acceptance Criteria**:
- [ ] Toggle control switches between views
- [ ] Graph view lazy loads when selected
- [ ] User preference persisted in localStorage
- [ ] Categories (Entry Points, Hubs, Leaves) work in both views
- [ ] Layout resize issues fixed
- [ ] View Connections button functional

**Story Points**: 8

**Labels**: `type: feature`, `area: frontend`, `priority: high`

---

### Tasks for Story 2

#### TASK-006: Implement View Toggle System

**Description**: Create the ViewToggle component and integrate dual-view system into App.tsx with lazy loading for the force graph.

**Technical Details**:
- Create `frontend/src/components/ViewToggle.tsx`
- Modify `frontend/src/App.tsx` to support view switching
- Implement React.lazy() for ForceGraph component
- Add Suspense with loading spinner
- Persist preference in localStorage under `codenav.defaultView`
- Add toggle control to header bar

**Acceptance Criteria**:
- [ ] Toggle control in header switches views
- [ ] ForceGraph lazy loads only when selected
- [ ] Loading spinner shown during graph load
- [ ] User preference saved to localStorage
- [ ] Preference restored on page load

**Effort**: M

**Parent Story**: STORY-002

**Labels**: `type: feature`, `area: frontend`

---

#### TASK-007: Update ToolsPanel with View Controls

**Description**: Enhance the ToolsPanel component with workbench-specific controls including view mode toggle and sort/filter options.

**Technical Details**:
- Modify `frontend/src/components/panels/ToolsPanel.tsx`
- Add grid/list view mode toggle
- Add sort dropdown (name, complexity, type, line)
- Ensure controls work in both views where applicable
- Add category quick access buttons

**Acceptance Criteria**:
- [ ] Grid/list toggle visible and functional
- [ ] Sort dropdown changes card ordering
- [ ] Category buttons filter to entry points/hubs/leaves
- [ ] Controls integrate with graphStore

**Effort**: M

**Parent Story**: STORY-002

**Labels**: `type: enhancement`, `area: frontend`

---

#### TASK-008: Implement Category Navigation

**Description**: Make the Entry Points, Hubs, and Leaves categories functional as quick filters that show relevant nodes.

**Technical Details**:
- Modify category selection in ToolsPanel
- Query `/api/graph/categories/{category}` endpoint
- Display category nodes in workbench canvas
- Show category badges on cards
- Support drilling into category items

**Acceptance Criteria**:
- [ ] Entry Points button shows nodes with no callers
- [ ] Hubs button shows highly connected nodes
- [ ] Leaves button shows nodes with no callees
- [ ] Each category node can be drilled into
- [ ] Badges shown on cards

**Effort**: M

**Parent Story**: STORY-002

**Labels**: `type: feature`, `area: frontend`

---

#### TASK-009: Fix Layout Resize Issues

**Description**: Fix the layout resize issues where the main panel doesn't resize correctly and the right panel sometimes disappears.

**Technical Details**:
- Convert layout to CSS Grid with minmax constraints
- Add ResizeObserver with window resize fallback
- Set minimum widths for panels
- Handle responsive breakpoints
- Test at various viewport sizes

**Acceptance Criteria**:
- [ ] Center panel resizes correctly on window resize
- [ ] Right panel never disappears
- [ ] Minimum widths prevent layout breaking
- [ ] Works on common screen sizes (1024, 1280, 1920)

**Effort**: M

**Parent Story**: STORY-002

**Labels**: `type: bug`, `area: frontend`, `priority: high`

---

#### TASK-010: Fix View Connections Button

**Description**: Make the View Connections button functional by implementing the connection loading and display in DetailsPanel.

**Technical Details**:
- Connect `onViewConnections` prop in DetailsPanel
- Query `/api/graph/query/callers` and `/api/graph/query/callees`
- Display connections list in DetailsPanel
- Allow navigation to connected nodes
- Show connection counts

**Acceptance Criteria**:
- [ ] View Connections button triggers connection load
- [ ] Callers list displayed
- [ ] Callees list displayed
- [ ] Clicking connection navigates to that node
- [ ] Loading state shown while fetching

**Effort**: M

**Parent Story**: STORY-002

**Labels**: `type: bug`, `area: frontend`, `priority: high`

---

## Story 3: Polish (Phase 3 - Week 3)

### STORY-003: User Experience Polish

**As a** power user  
**I want** keyboard navigation and refined interactions  
**So that** I can navigate efficiently without relying solely on mouse

**Acceptance Criteria**:
- [ ] Arrow keys navigate between cards
- [ ] Enter drills into selected card
- [ ] Escape goes back one level
- [ ] Loading states for all async operations
- [ ] Smooth transitions between views
- [ ] Sort and filter controls functional

**Story Points**: 8

**Labels**: `type: enhancement`, `area: frontend`, `priority: medium`

---

### Tasks for Story 3

#### TASK-011: Add Keyboard Navigation

**Description**: Implement keyboard navigation for the workbench view using arrow keys, Enter, and Escape.

**Technical Details**:
- Add keyboard event handlers to WorkbenchCanvas
- Implement focus management for card grid
- Arrow keys move selection between cards
- Enter drills into selected card
- Escape goes back one level
- Tab for accessibility

**Acceptance Criteria**:
- [ ] Arrow keys move selection
- [ ] Enter activates selected card
- [ ] Escape navigates back
- [ ] Focus visible indicator on selected card
- [ ] Works with screen readers

**Effort**: M

**Parent Story**: STORY-003

**Labels**: `type: enhancement`, `area: frontend`

---

#### TASK-012: Add Loading States and Transitions

**Description**: Add proper loading states and smooth transitions for view switching and data loading.

**Technical Details**:
- Add loading skeletons for cards
- Add transition animations for drill-down
- Show loading indicator during data fetch
- Animate view toggle transition
- Handle error states gracefully

**Acceptance Criteria**:
- [ ] Skeleton loaders shown while loading
- [ ] Smooth fade/slide for drill-down
- [ ] View toggle animates smoothly
- [ ] Error states display helpful message
- [ ] No layout shift during loading

**Effort**: M

**Parent Story**: STORY-003

**Labels**: `type: enhancement`, `area: frontend`

---

#### TASK-013: Implement Grid/List View Toggle

**Description**: Allow users to switch between grid and list views for child nodes in the workbench.

**Technical Details**:
- Add toggle control in ToolsPanel
- Persist preference in localStorage
- Grid view: responsive card grid
- List view: compact table/list rows
- Both support same interactions

**Acceptance Criteria**:
- [ ] Toggle switches between views
- [ ] Preference persisted
- [ ] Grid view responsive
- [ ] List view compact and scannable
- [ ] Same actions available in both

**Effort**: S

**Parent Story**: STORY-003

**Labels**: `type: enhancement`, `area: frontend`

---

#### TASK-014: Add Sort/Filter Controls

**Description**: Implement sorting and filtering controls for the workbench child nodes.

**Technical Details**:
- Add sort dropdown (name, complexity, type, lines)
- Add filter input for search within children
- Remember last sort preference
- Real-time filter as user types
- Clear filter button

**Acceptance Criteria**:
- [ ] Sort by name, complexity, type, lines
- [ ] Filter input searches children
- [ ] Sort preference persisted
- [ ] Filter updates in real-time
- [ ] Clear button resets filter

**Effort**: S

**Parent Story**: STORY-003

**Labels**: `type: enhancement`, `area: frontend`

---

#### TASK-015: Performance Optimization for Large Node Sets

**Description**: Optimize workbench view performance for codebases with 1000+ nodes.

**Technical Details**:
- Implement virtualized list for list view
- Lazy render cards not in viewport
- Cache child node data
- Debounce search/filter
- Profile and optimize re-renders

**Acceptance Criteria**:
- [ ] Smooth scrolling with 1000+ nodes
- [ ] Initial render under 500ms
- [ ] No visible lag during filtering
- [ ] Memory usage acceptable

**Effort**: L

**Parent Story**: STORY-003

**Labels**: `type: enhancement`, `area: frontend`, `priority: medium`

---

## Story 4: Testing (Phase 4 - Week 4)

### STORY-004: Comprehensive Test Coverage

**As a** maintainer  
**I want** comprehensive test coverage for the workbench view  
**So that** future changes don't break functionality

**Acceptance Criteria**:
- [ ] 80%+ code coverage on new components
- [ ] Playwright E2E tests for all user flows
- [ ] Vitest component tests for all components
- [ ] Visual regression tests for layouts
- [ ] Tests run in CI pipeline

**Story Points**: 5

**Labels**: `type: testing`, `area: frontend`, `priority: high`

---

### Tasks for Story 4

#### TASK-016: Complete Playwright E2E Test Suite

**Description**: Finalize the Playwright E2E test suite with comprehensive coverage of workbench functionality.

**Technical Details**:
- Complete Page Object Models
- Add tests for all navigation flows
- Test view toggle functionality
- Test category navigation
- Test resize behavior
- Test keyboard navigation

**Acceptance Criteria**:
- [ ] Navigation flow tests complete
- [ ] View toggle tests complete
- [ ] Category tests complete
- [ ] Keyboard navigation tests complete
- [ ] All tests pass in CI

**Effort**: M

**Parent Story**: STORY-004

**Labels**: `type: testing`, `area: frontend`

---

#### TASK-017: Add Vitest Component Tests

**Description**: Add unit tests for all new workbench components using Vitest.

**Technical Details**:
- Test WorkbenchCanvas
- Test NodeCard (all variants)
- Test BreadcrumbNavigation
- Test ViewToggle
- Mock graphStore for isolation

**Acceptance Criteria**:
- [ ] WorkbenchCanvas tests
- [ ] NodeCard tests (3 variants)
- [ ] BreadcrumbNavigation tests
- [ ] ViewToggle tests
- [ ] 80%+ coverage on new components

**Effort**: M

**Parent Story**: STORY-004

**Labels**: `type: testing`, `area: frontend`

---

#### TASK-018: Visual Regression Testing Setup

**Description**: Set up visual regression testing to catch unintended UI changes.

**Technical Details**:
- Configure Playwright for screenshot comparison
- Create baseline screenshots
- Set up snapshot storage
- Document threshold settings
- Add to CI pipeline

**Acceptance Criteria**:
- [ ] Screenshot comparison configured
- [ ] Baseline screenshots captured
- [ ] Threshold for acceptable diff set
- [ ] Works in CI environment

**Effort**: M

**Parent Story**: STORY-004

**Labels**: `type: testing`, `area: infra`

---

#### TASK-019: CI/CD Integration for Tests

**Description**: Integrate all new tests into the CI/CD pipeline with proper gates.

**Technical Details**:
- Add Playwright tests to CI workflow
- Add Vitest tests to CI workflow
- Add visual regression to CI
- Set up test result reporting
- Configure failure notifications

**Acceptance Criteria**:
- [ ] Playwright tests run on PR
- [ ] Vitest tests run on PR
- [ ] Visual regression runs on PR
- [ ] Test results visible in PR
- [ ] Failed tests block merge

**Effort**: S

**Parent Story**: STORY-004

**Labels**: `type: chore`, `area: infra`

---

## Bug Fixes (Tracked Separately)

These bugs are mentioned in the "Known Issues to Track" section of the design doc but overlap with Story 2:

| Bug ID | Title | Addressed In |
|--------|-------|--------------|
| BUG-001 | Main panel resize issue | TASK-009 |
| BUG-002 | Right panel disappears | TASK-009 |
| BUG-003 | View Connections non-functional | TASK-010 |

---

## Future Features (Backlog)

These are mentioned in the "Features" subsection of "Known Issues to Track" and should be created as backlog items:

| Feature | Description | Priority |
|---------|-------------|----------|
| Multi-select | Ctrl+click to select multiple nodes for comparison | Low |
| Drag-and-drop | Reorder cards in custom order | Low |
| Export view | Screenshot/export current view | Low |

---

## Label Reference

| Label | Color | Usage |
|-------|-------|-------|
| `type: feature` | Purple | New functionality |
| `type: enhancement` | Blue | Improvement to existing |
| `type: bug` | Red | Something broken |
| `type: testing` | Green | Test coverage |
| `type: chore` | Gray | Maintenance |
| `area: frontend` | Cyan | React/TypeScript |
| `area: infra` | Blue | CI/CD, Docker |
| `priority: high` | Orange | Should be done soon |
| `priority: medium` | Yellow | Standard priority |

---

## Summary

| Item | Count |
|------|-------|
| Epic | 1 |
| Stories | 4 |
| Tasks | 19 |
| Bugs (addressed) | 3 |
| Future features | 3 |
| **Total Issues to Create** | **24** |

---

*This document was generated by the Sprint Planner Agent from the Workbench View Design Document.*
