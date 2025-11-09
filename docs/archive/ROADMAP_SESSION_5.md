# Session 5 Roadmap: Backend Query API + Tool Execution UI

**Date**: 2025-11-01 (Planning)  
**Estimated Duration**: 4-6 hours  
**Priority**: High (blocks tool execution from UI)

---

## Overview

Session 5 will implement the backend query API endpoints that the frontend is already prepared for, then build a tool execution panel in the frontend.

**Current State**:
- ✅ Frontend has RelationshipBrowser component
- ✅ Frontend has TraversalControls component
- ✅ Frontend has store methods for findCallers, findCallees, findReferences
- ❌ Backend endpoints don't exist yet
- ❌ Frontend has no ToolPanel component yet

---

## Phase 1: Implement Backend Query Endpoints (2-3 hours)

### Objective
Add three missing REST API endpoints to handle graph queries.

### Endpoints to Implement

#### 1. GET /api/graph/query/callers
**Purpose**: Find all functions that call a given symbol  
**Request**: `?symbol=function_name`  
**Response**:
```json
{
  "results": [
    {"caller": "func_a", "caller_id": "...", "file": "...", "line": 42},
    {"caller": "func_b", "caller_id": "...", "file": "...", "line": 89}
  ],
  "count": 2,
  "execution_time_ms": 45
}
```

**Implementation Location**: `src/code_graph_mcp/server/graph_api.py`  
**Implementation Steps**:
1. Add route decorator: `@router.get("/query/callers")`
2. Extract symbol from query params
3. Call `analysis_engine.find_function_callers(symbol)`
4. Format results as per response schema
5. Return with timing

#### 2. GET /api/graph/query/callees
**Purpose**: Find all functions called by a given symbol  
**Request**: `?symbol=function_name`  
**Response**:
```json
{
  "results": [
    {"callee": "func_x", "callee_id": "...", "file": "...", "line": 12},
    {"callee": "func_y", "callee_id": "...", "file": "...", "line": 34}
  ],
  "count": 2,
  "execution_time_ms": 38
}
```

**Implementation**: Same pattern as callers endpoint

#### 3. GET /api/graph/query/references
**Purpose**: Find all references to a given symbol  
**Request**: `?symbol=symbol_name`  
**Response**:
```json
{
  "results": [
    {"referencing_symbol": "func_a", "referencing_id": "...", "file": "...", "line": 55},
    {"referencing_symbol": "func_b", "referencing_id": "...", "file": "...", "line": 77}
  ],
  "count": 2,
  "execution_time_ms": 52
}
```

**Implementation**: Same pattern as callers/callees

### Implementation Checklist

- [ ] Create response DTO classes (if not present)
  - QueryCallerResult
  - QueryCalleeResult
  - QueryReferenceResult
  - QueryResultsResponse

- [ ] Add routes to graph_api.py
  - [ ] GET /query/callers
  - [ ] GET /query/callees
  - [ ] GET /query/references

- [ ] Test endpoints manually with curl
  ```bash
  curl "http://localhost:8000/api/graph/query/callers?symbol=analyze_project"
  curl "http://localhost:8000/api/graph/query/callees?symbol=analyze_project"
  curl "http://localhost:8000/api/graph/query/references?symbol=UniversalParser"
  ```

- [ ] Add unit tests for each endpoint
  - [ ] tests/test_query_endpoints.py (NEW)
  - Test valid symbol names
  - Test non-existent symbols (should return 0 results)
  - Test performance (should be fast)

- [ ] Update CRUSH.md with endpoint definitions

---

## Phase 2: Frontend Tool Execution Panel (2-3 hours)

### Objective
Build a component to discover and execute MCP tools from the UI.

### Components to Build

#### 1. ToolPanel.vue (NEW)
**Purpose**: Main tool discovery and execution interface  
**Location**: `frontend/src/components/ToolPanel.vue`

**Features**:
- [ ] Dropdown to select tool
- [ ] Dynamic form based on tool schema
- [ ] Execute button
- [ ] Results display area
- [ ] Loading state
- [ ] Error handling

**Schema**:
```vue
<template>
  <div class="space-y-3">
    <div>
      <label class="text-xs font-medium text-gray-300">Tool</label>
      <select v-model="selectedTool" class="w-full px-2 py-1 text-sm ...">
        <option value="">-- Select a tool --</option>
        <option value="find_callers">Find Callers</option>
        <option value="find_callees">Find Callees</option>
        <option value="find_references">Find References</option>
        <option value="analyze_codebase">Analyze Codebase</option>
        <option value="project_statistics">Project Statistics</option>
      </select>
    </div>

    <!-- Dynamic form for tool parameters -->
    <div v-if="selectedTool && currentToolSchema">
      <FormBuilder :schema="currentToolSchema" v-model="toolParams" />
    </div>

    <!-- Execute button -->
    <button @click="executeTool" :disabled="!canExecute">
      {{ isExecuting ? '⟳ Executing...' : '▶ Execute' }}
    </button>

    <!-- Results -->
    <div v-if="toolResults" class="bg-gray-800 rounded p-2 text-xs">
      <div v-for="(result, i) in toolResults" :key="i" class="py-1">
        {{ JSON.stringify(result) }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// Implementation
</script>
```

#### 2. FormBuilder.vue (NEW - Optional)
**Purpose**: Dynamic form generation from tool schema  
**Complexity**: Medium  
**Use Case**: Build form inputs based on tool parameter definitions

**Alternative**: Use ToolPanel with hardcoded forms for each tool (simpler)

### Implementation Checklist

- [ ] Create ToolPanel.vue component
  - [ ] Tool selection dropdown
  - [ ] Dynamic parameter form or hardcoded forms
  - [ ] Execute button with loading state
  - [ ] Results display
  - [ ] Error message display

- [ ] Create FormBuilder.vue (optional)
  - [ ] Text input field
  - [ ] Number input field
  - [ ] Checkbox
  - [ ] Select dropdown
  - [ ] Nested objects

- [ ] Add tool definitions
  - [ ] Create ToolDefinition interface in types/
  - [ ] Define tool schemas (tools/toolDefinitions.ts)

- [ ] Integrate into App.vue
  - [ ] Add ToolPanel to a new panel or modal
  - [ ] Show in bottom-right corner or as new tab
  - [ ] Only show when needed (button to toggle)

- [ ] Connect to backend
  - [ ] Create api/toolClient.ts
  - [ ] Methods: executeTool, getToolSchema, listTools
  - [ ] Handle tool execution responses

- [ ] Write tests
  - [ ] tests/components/ToolPanel.spec.ts (if needed)

---

## Phase 3: Integration Testing (1 hour)

### Test Plan

- [ ] Start Docker stack with both services
- [ ] Test each query endpoint with curl
- [ ] Test frontend ToolPanel loads tools
- [ ] Test executing a tool from UI
- [ ] Verify results display correctly
- [ ] Test error cases (non-existent symbol, etc)

### Integration Test Checklist

- [ ] Docker compose up -d
- [ ] Frontend loads without errors
- [ ] Graph renders with nodes
- [ ] Click node → relationships appear
- [ ] Click relationship → navigate to node
- [ ] Open ToolPanel dropdown
- [ ] Select "Find Callers"
- [ ] See form with symbol input
- [ ] Execute tool
- [ ] See results in ToolPanel
- [ ] Results match backend

---

## File Changes Summary

### Backend Files (Phase 1)
```
src/code_graph_mcp/server/
├── graph_api.py (ADD: 3 endpoints, ~100 lines)
└── [existing response models]

tests/
├── test_query_endpoints.py (NEW, ~150 lines)
└── test_graph_api.py (may add to)
```

### Frontend Files (Phase 2)
```
frontend/src/
├── components/
│   ├── ToolPanel.vue (NEW, ~150 lines)
│   └── FormBuilder.vue (OPTIONAL, ~100 lines)
├── api/
│   ├── graphClient.ts (already has stubs)
│   └── toolClient.ts (NEW, ~50 lines)
├── types/
│   ├── graph.ts (existing QueryResultsResponse)
│   └── tools.ts (NEW, ~30 lines)
├── utils/
│   └── toolDefinitions.ts (NEW, ~100 lines)
└── App.vue (ADD: ToolPanel integration, ~10 lines)
```

---

## Success Criteria

### Phase 1 (Backend) ✅ = 
- [ ] All 3 endpoints implemented
- [ ] Endpoints return correct response format
- [ ] Endpoints handle non-existent symbols gracefully
- [ ] Execution time < 200ms for reasonable queries
- [ ] Tests pass (100% coverage for new endpoints)

### Phase 2 (Frontend) ✅ = 
- [ ] ToolPanel component renders without errors
- [ ] Tool dropdown populates correctly
- [ ] Form renders for selected tool
- [ ] Execute button works
- [ ] Results display in UI
- [ ] Error messages show for failed executions

### Phase 3 (Integration) ✅ = 
- [ ] Can execute tool from UI
- [ ] Results appear in frontend
- [ ] No console errors
- [ ] Performance acceptable (< 2s round trip)

---

## Estimated Timeline

| Phase | Task | Hours | Status |
|-------|------|-------|--------|
| 1 | Backend endpoints | 2-3 | Not started |
| 2 | Frontend ToolPanel | 2-3 | Not started |
| 3 | Integration testing | 1 | Not started |
| - | **TOTAL** | **5-7** | - |

---

## Commands Reference

### Test Endpoints (After Implementation)
```bash
# Find callers
curl "http://localhost:8000/api/graph/query/callers?symbol=analyze_project"

# Find callees
curl "http://localhost:8000/api/graph/query/callees?symbol=analyze_project"

# Find references
curl "http://localhost:8000/api/graph/query/references?symbol=UniversalParser"
```

### Run Tests
```bash
# Backend tests
pytest tests/test_query_endpoints.py -v

# Full suite
pytest tests/ --ignore=tests/quarantine -v
```

### Frontend Dev
```bash
cd frontend
npm run dev  # http://localhost:5173
```

---

## Dependencies & Assumptions

- **Backend**: All necessary analysis_engine methods exist (verified in Phase 1)
- **Frontend**: GraphClient already has method stubs for queries
- **API**: Base URL is /api (configured in graphClient)
- **Tools**: MCP tools already work via CLI

---

## Known Risks & Mitigations

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Backend endpoints slow | Medium | Add caching layer if needed |
| Form builder complexity | Medium | Start with hardcoded forms |
| Test isolation issues | Low | Use module-scoped fixtures |
| Frontend build issues | Low | Restart dev server if needed |

---

## Branching Strategy

```
Session 5 Work:
main
├── feature/backend-query-endpoints
│   ├── [query endpoint implementations]
│   └── [query endpoint tests]
└── feature/frontend-tool-panel
    ├── [ToolPanel component]
    ├── [FormBuilder component]
    └── [App.vue integration]

Merge back to main at end of each phase
```

---

## Quick Links

- Backend API: `src/code_graph_mcp/server/graph_api.py`
- Frontend API: `frontend/src/api/graphClient.ts`
- Test Commands: See tests/ directory
- Frontend Docs: `frontend/DEV_GUIDE.md`
- Docker Docs: `frontend/DOCKER.md`

---

## Next Steps (After Session 4 Complete)

1. ✅ Understand current backend/frontend state (read SESSION_4_COMPLETION.md)
2. ✅ Review query endpoint requirements (in this file)
3. Start Phase 1: Backend endpoints
4. Start Phase 2: Frontend ToolPanel
5. Run integration tests
6. Deploy and celebrate! 🎉
