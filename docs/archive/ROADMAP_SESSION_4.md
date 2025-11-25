# Session 4 Roadmap: Backend Stabilization + UI Navigation

**Date**: 2025-11-01  
**Focus**: Make MCP/Redis persistence rock-solid, then enhance UI navigation  
**Prime Directive**: Useful MCP with Redis persistence

---

## Current State Assessment

### ✅ Working
- **Backend Core**: 458 nodes, 4157 relationships in graph
- **API Endpoints**: 7 endpoints functional (stats, search, traverse, etc)
- **Graph Tests**: 6/15 tests passing in test_graph_api.py
- **MCP Tools**: Basic tools callable (analyze_codebase, find_references, etc)
- **Docker**: Full stack runs (frontend, HTTP server, Redis)
- **Frontend**: Renders graph with Cytoscape, shows 458 nodes

### 🔴 Critical Issues (Blocking)
1. **Frontend Error**: "Cannot read properties of undefined (reading 'forEach')" - graph rendering crashes
2. **Test Failures**: 10 tests failing in test_graph_queries.py (AsyncIO fixture issues + AttributeErrors)
3. **Test Errors**: 9 test files won't import (missing classes, broken syntax, missing deps)
4. **Graph Query Tools**: Zero results on find_references, find_callers, find_callees despite 2025-10-30 fix

### 🟡 Secondary Issues
- Frontend TypeScript error: missing App.vue type declarations
- UI has no navigation controls (can't click nodes to traverse)
- No UX component library (using Tailwind only)
- Limited error handling in frontend/backend API calls

---

## Priority 1: Backend Stabilization (Days 1-2)

### Phase 1a: Fix Test Infrastructure
**Goal**: Get all valid tests passing, delete/quarantine broken ones

1. **Fix test_graph_queries.py failures** (10 failing)
   - Issue: AsyncIO fixture deprecation warnings
   - Action: Convert @pytest.fixture to @pytest_asyncio.fixture for async fixtures
   - Files: tests/test_graph_queries.py
   - Expected: 10 → 9/9 passing

2. **Fix broken test files** (delete or quarantine)
   - tests/test_analysis.py: Syntax error (line 5 backslash issue) → DELETE or FIX
   - tests/test_mcp_cache_integration.py: Import error (CacheManager) → QUARANTINE
   - tests/test_mcp_http.py: Missing aiohttp → QUARANTINE or ADD TO DEPS
   - tests/test_mcp_rustworkx_integration.py: Module doesn't exist → DELETE
   - tests/test_redis_cache.py: Import error → QUARANTINE
   - tests/test_rustworkx_graph.py: Module doesn't exist → DELETE
   - tests/test_rustworkx_performance.py: Module doesn't exist → DELETE
   - tests/test_sse_server.py: Import error (SSECodeGraphServer) → QUARANTINE
   - tests/test_zero_results_diagnosis.py: Import error → QUARANTINE

3. **Run clean test suite** (targeting 85+ passing tests)
   ```bash
   pytest tests/ -k "not (analysis or cache_integration or mcp_http or rustworkx or redis_cache or sse_server or zero_results)" -v
   ```

### Phase 1b: Fix Graph Query Tools
**Goal**: find_callers, find_callees, find_references return correct results

1. **Diagnosis Test**
   - Run: `pytest tests/test_query_tools_live.py -v`
   - Check if the 2025-10-30 CALLS extraction is working

2. **If failing**: Verify _extract_function_calls_ast() is being called in UniversalParser
   - Check parser initialization in analysis_engine.py
   - Ensure CALLS relationships are created during parse

3. **Write focused test**
   - Create tests/test_backend_graph_queries.py
   - Test: "function X calls function Y" → find_callers(Y) returns X
   - Test across multiple languages (Python, TypeScript, etc)

### Phase 1c: Redis Persistence Deep Dive
**Goal**: Verify cache_manager persists data correctly across restarts

1. **Test Redis connectivity in isolation**
   - Create tests/test_redis_integration.py
   - Test: Write node → Redis → Read node (same id)
   - Test: Clear Redis → Write new nodes → Verify count

2. **Docker compose persistence test**
   - Spin up stack, analyze code (458 nodes)
   - Stop container, restart
   - Verify same 458 nodes loaded from Redis
   - If failing: Debug Redis key structure, TTL settings

3. **Add metrics logging**
   - Log cache hits/misses per operation
   - Add timing for Redis latency
   - Use in production diagnostics

---

## Priority 2: Frontend Navigation (Days 2-3)

### Phase 2a: Fix Rendering Error
**Goal**: Graph renders without console errors

1. **Debug "forEach" error**
   - Check GraphViewer.vue line 95-115 (the updateGraph function)
   - Verify graphStore.nodeArray/edgeArray are arrays, not undefined
   - Add null checks + optional chaining

2. **Add error boundary**
   - Catch errors in GraphViewer and render fallback
   - Log to console for debugging

3. **Test in browser**: Graph should render all nodes without crashing

### Phase 2b: Add Graph Navigation
**Goal**: Users can click nodes and traverse relationships

**New Components**:

1. **NodeContextMenu.vue**
   - Show on right-click: "Find Callers", "Find Callees", "Find References"
   - Call API endpoints
   - Load results into sidebar

2. **RelationshipBrowser.vue**
   - Display relationships from selected node
   - Group by type: CALLS, CONTAINS, IMPORTS, SEAMS
   - Click relationship → navigate to related node

3. **TraversalControls.vue** (enhanced SearchBar)
   - Add "Traverse Up" / "Traverse Down" buttons
   - Depth slider (1-5 levels)
   - Direction toggle

4. **Enhanced NodeDetails.vue**
   - Show relationships section
   - Links to related nodes (clickable)
   - Call count, import count, etc

### Phase 2c: UI Polish (Optional - Low Priority)
**Component Library Decision**:
- ✅ **Stick with Tailwind + Headless UI** (no extra deps)
- Already in package.json, minimal overhead
- Build custom components as needed
- Keeps bundle small for Docker container

**Alternative**: Shadcn/vue (Tailwind-based, Vue 3, copy-paste components)
- Minimal setup, good looking
- Decision: Try this for 2-3 components, decide based on DX

---

## Priority 3: MCP Tools Callable from UI (Days 3-4)

### Phase 3a: MCP Tool Integration
**Goal**: Run analyze_codebase, find_references, etc from frontend

1. **Create ToolPanel.vue component**
   - Dropdown: select MCP tool
   - Dynamic form based on tool schema
   - Call /api/tools/execute endpoint

2. **Backend: Add /api/tools/execute endpoint**
   - Endpoint: POST /api/tools/execute
   - Body: { tool_name: "find_callers", params: { symbol: "create_graph_api" } }
   - Response: { results: [...], execution_time_ms: 123 }

3. **Test with UI**
   - Select "find_callers" tool
   - Enter symbol name
   - See results in popup

### Phase 3b: Results Display
**Goal**: Show tool results in graph and sidebar

1. **Highlight found nodes** in graph (color = result)
2. **Show execution stats**: "Found 5 results in 42ms"
3. **Export results**: Download JSON/CSV

---

## Code Changes Summary

### Backend (src/codenav/)
```
Priority 1 - Test Fixes:
  - tests/test_graph_queries.py: Fix async fixtures
  - tests/: Delete/quarantine broken tests
  - tests/test_backend_graph_queries.py: NEW focused tests
  - tests/test_redis_integration.py: NEW Redis persistence tests

Priority 2 - (No code changes needed)

Priority 3 - New APIs:
  - src/codenav/server/graph_api.py: Add /api/tools/execute endpoint
```

### Frontend (frontend/src/)
```
Priority 2a - Bug Fixes:
  - components/GraphViewer.vue: Add null checks, error handling
  - components/App.vue: Global error boundary

Priority 2b - Navigation (NEW):
  - components/NodeContextMenu.vue: NEW
  - components/RelationshipBrowser.vue: NEW
  - components/TraversalControls.vue: Enhanced SearchBar
  - components/NodeDetails.vue: Enhanced with relationships
  - stores/graphStore.ts: Add selectedRelationships state

Priority 3 - Tools UI (NEW):
  - components/ToolPanel.vue: NEW
  - api/graphClient.ts: Add executeToolAction() method
```

---

## Testing Strategy

### Backend Testing (Pytest)
```bash
# Phase 1a: Core tests
pytest tests/test_graph_api.py -v

# Phase 1b: Query tools
pytest tests/test_query_tools_live.py -v

# Phase 1c: Redis
pytest tests/test_redis_integration.py -v  # NEW

# Phase 1 full
pytest tests/ -k "not (analysis or cache_integration or mcp_http or rustworkx or redis_cache or sse_server or zero_results)" -v
```

### Frontend Testing (Manual in browser)
- http://localhost:5173
- Visual: Graph renders without errors
- Interaction: Click nodes, see details
- Navigation: Right-click → traverse options

### Integration Testing (Docker)
```bash
compose down
docker volume rm codenav-repo-mount  # Or change mount path
compose up
# Verify in UI: http://localhost:5173
```

---

## Success Criteria

### Backend
- ✅ 80+ tests passing (up from 6)
- ✅ Redis persists 458 nodes across restarts
- ✅ find_callers, find_references, find_callees return non-empty results
- ✅ No import errors when running pytest

### Frontend
- ✅ Graph renders without "forEach" error
- ✅ Can click nodes and see details
- ✅ Right-click context menu works
- ✅ Can run MCP tools from UI

### Deliverables
- ROADMAP_SESSION_4_COMPLETE.md (this document filled in with results)
- tests/test_redis_integration.py (NEW, 8+ tests)
- tests/test_backend_graph_queries.py (NEW, focused query tests)
- Updated components/ with navigation UI
- Updated API endpoints for tool execution

---

## Timeline Estimate
- Phase 1a (Tests): 4-6 hours
- Phase 1b (Queries): 2-4 hours
- Phase 1c (Redis): 2-3 hours
- Phase 2a (Fix Error): 1-2 hours
- Phase 2b (Navigation): 6-8 hours
- Phase 2c (Polish): 2-4 hours (optional)
- Phase 3 (Tools): 4-6 hours

**Total**: 21-33 hours, **Priority 1 (Backend): 8-13 hours** ← Start here
