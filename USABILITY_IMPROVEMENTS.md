# Code Graph MCP - Usability Improvements Needed

## Session Testing Summary (2025-11-02)

**Status**: Frontend loads without errors, basic graph rendering works
**Testing Method**: Playwright browser automation

---

## Critical Issues Found

### 1. Graph Not Visible / Too Small
**Problem**: Graph canvas likely shows nodes but they may be tiny/clustered
**Root Cause**: 
- Initial traverse likely loads ALL 908 nodes at once
- No initial zoom/fit applied
- Nodes may be overlapping

**Fix Needed**:
- Limit initial load to 20-50 nodes max
- Add automatic fit() call after first render
- Set better default zoom level
- Add zoom controls (+ / - buttons)

### 2. Double-Click Expand Not Tested
**Problem**: Core feature (expand on double-click) not validated
**Needs Testing**:
- Can users actually double-click nodes?
- Does expand fetch data correctly?
- Do new nodes appear in expected locations?
- Performance with incremental loading?

### 3. No Pan/Zoom Controls Visible
**Problem**: Users can't easily navigate large graphs
**Missing**:
- Mouse wheel zoom
- Click+drag panning  
- Zoom in/out buttons
- Reset view button
- Minimap for orientation

### 4. Layout Issues
**Problem**: Hierarchical layout may not work well with 900+ nodes
**Observations**:
- Breadthfirst from entry points might create huge vertical trees
- DAG layout probably better for large graphs
- Circle layout unusable for >100 nodes

**Fix Needed**:
- Default to DAG layout for large graphs (>100 nodes)
- Add "Collapse All" / "Expand All" buttons
- Implement graph sampling (show top N most connected nodes)

### 5. Entry Point Detection Unclear
**Problem**: 63 entry points detected but users can't see which ones
**Needs**:
- Visual indicator in UI showing count
- Filter to show only entry points
- Jump to entry point dropdown
- Highlight entry points in different color/size

### 6. Performance Not Tested
**Concerns**:
- Rendering 908 nodes + 14068 edges at once
- Client-side graph likely freezes browser
- No loading indicators during expand
- No cancellation of long-running operations

**Fix Needed**:
- Implement graph virtualization/culling
- Show progress bars during data fetch
- Add "Cancel" button for long operations
- Lazy render edges (only show when zoomed in)

---

## Moderate Issues

### 7. Search Doesn't Auto-Traverse
**Problem**: Searching finds nodes but doesn't load them into graph
**Expected**: Search result click should trigger traverse + zoom to node

### 8. Tool Panel Results Not Clickable
**Problem**: Query results show but clicking doesn't add to graph
**Expected**: Click result → add node → highlight in graph

### 9. No Keyboard Shortcuts
**Missing**:
- `Esc` to deselect
- `F` to fit graph
- `+/-` to zoom
- Arrow keys to pan
- `Delete` to remove selected node

### 10. Mobile/Responsive Issues
**Not Tested**: Likely broken on mobile due to:
- Fixed sidebar widths
- No touch pan/zoom
- Small buttons
- Tiny node labels

---

## Minor Polish Needed

### 11. No Loading States
- "Fetching callers..." spinner missing
- "Expanding node..." message missing
- Progress bar for large traversals

### 12. Empty States Unclear
- "No graph loaded" should show call-to-action
- "No results found" should suggest alternatives
- "No relationships" could show "Add connections" hint

### 13. Error Messages Generic
- "Failed to traverse" → show actual error
- "No nodes found" → suggest using search
- Errors should have "Retry" button

### 14. Legend Not Interactive
- Legend items should be clickable filters
- "Hide entry points" / "Show only hubs"
- Click SEAM legend → filter to SEAM edges only

### 15. No Export/Share
**Missing**:
- Export graph as PNG
- Export as GraphML/JSON
- Share link with current view state
- Permalink to specific node

---

## Recommended Priorities

### Phase 1 (Critical - 2 hours)
1. Limit initial load to 50 nodes
2. Add zoom controls (mousewheel + buttons)
3. Fix layout defaults (DAG for large graphs)
4. Add loading spinners for all async operations

### Phase 2 (High - 3 hours)
5. Make search results clickable → traverse
6. Make tool results clickable → add to graph
7. Add keyboard shortcuts (Esc, F, +, -)
8. Implement entry point dropdown/filter

### Phase 3 (Medium - 4 hours)
9. Add graph sampling/virtualization
10. Implement pan/zoom with mouse
11. Add export to PNG feature
12. Create interactive legend filters

### Phase 4 (Polish - 2 hours)
13. Better empty states with CTAs
14. Improve error messages + retry
15. Add loading progress indicators
16. Responsive layout fixes

---

## Testing Checklist (Playwright)

- [ ] Navigate to http://localhost:5173
- [ ] Verify graph canvas visible
- [ ] Click a node → details appear in sidebar
- [ ] Double-click a node → new nodes appear
- [ ] Change layout → graph re-renders
- [ ] Use search → find node → click → loads in graph
- [ ] Execute query tool → results appear → click result → highlights node
- [ ] Test zoom in/out
- [ ] Test pan (drag background)
- [ ] Test filter panel → toggle language → graph updates
- [ ] Test "Clear" button → graph clears
- [ ] Test "Fit" button → graph centers
- [ ] Test "Center" on selected node

---

## Performance Targets

- **Initial Load**: < 2 seconds for 50 nodes
- **Node Expand**: < 500ms for 10 callers/callees  
- **Layout Recalculation**: < 1 second for 100 nodes
- **Zoom/Pan**: 60 FPS smooth
- **Search**: < 100ms for autocomplete

---

## Browser Compatibility

**Tested**: Playwright (Chromium-based)
**Needs Testing**: 
- Firefox
- Safari
- Mobile Chrome/Safari
- Edge

---

*Generated: 2025-11-02*
*Session: Feature Enhancement (Styling + Interactive Graph)*
