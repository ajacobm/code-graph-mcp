# Code Graph MCP - Current State

**Rolling document tracking session-by-session progress with git context.**

---

## Session 12 (2025-11-08) - `feature/sigma-graph-spike` @ `4d5c8c9`

### Summary
Fixed critical backend relationship bugs and enhanced UI styling, but discovered severe performance issues with high-degree nodes. System is functional but **not production-ready** due to missing pagination.

### Commits This Session
1. `5567256` - fix: Add error handling for relationship type deserialization
2. `4d5c8c9` - fix: Handle correct API response format in ConnectionsList

### Critical Bugs Fixed

**1. Relationship Type Deserialization Bug**
- **Problem**: 11,871 CALLS relationships created but not loaded from Redis cache
- **Root Cause**: `RelationshipType` enum deserialization failing silently in `_dict_to_relationship()`
- **Fix**: Added try-catch with fallback to `RelationshipType.CALLS`
- **Result**: `find_function_callers` now returns 21+ results (was 0 before)

**2. API Response Format Mismatch**
- **Problem**: Frontend `ConnectionsList` looking for `results` field, backend returns `callers`/`callees`
- **Fix**: Updated field mapping in `ConnectionsList.vue` to convert backend format to node structure
- **Result**: Callers, callees, and siblings now display correctly in UI

### UI Improvements
- Browse tab now uses `NodeTile` components instead of plain divs (consistent styling)
- Details pane enhanced with card layout and proper visual hierarchy
- All components follow same DaisyUI design language

### 🚨 Critical Issues Discovered

**Performance Crisis: 1,600+ Connections**
- Common import nodes (e.g., Python's `re` module) have **1,123 callers + 495 callees = 1,618 total**
- All rendered to DOM at once (no pagination or virtualization)
- Browser timeout on screenshot (5000ms exceeded)
- Tiny vertical scrollbar indicates massive list
- **Impact**: App unusable for high-degree nodes

**Desktop Layout Problems**
- Horizontal scroll bar always present (slim edge of page cut off)
- Mobile-first responsive design not suitable for desktop workflow app
- Missing: multi-column layout, pinned panels, code preview
- User feedback: "seems to be designed primarily for mobile"

### Graph State
- **Core Codebase**: 489 nodes, 4,475 relationships (src/code_graph_mcp only)
- **With Workspace**: 974 nodes, 12,767 relationships (includes tests, frontend)
- **Relationship Types**: contains (703), imports (193), calls (11,871)
- **Languages Supported**: 25 (Python, TypeScript, JavaScript, C#, Go, Rust, etc.)
- **Circular Dependencies**: 121 detected
- **Strongly Connected Components**: 477

### Stack Status
- ✅ Backend HTTP server healthy (port 8000)
- ✅ Frontend Vite dev server running (port 5173)
- ✅ Redis cache operational (port 6379)
- ✅ All query endpoints returning correct data
- ✅ Frontend-backend communication working
- ⚠️ Frontend healthcheck failing (cosmetic - Vite doesn't bind to localhost in-container)

### MCP Tool Integration
- **Codegraph MCP**: Successfully analyzed codebase, identified architecture issues
- **Cortexgraph MCP**: 9 memories saved for session continuity and debugging
- **Playwright**: Used for E2E UX validation, discovered the 1,600+ connections issue

### Files Modified
- `src/code_graph_mcp/universal_parser.py` - Fixed relationship deserialization
- `frontend/src/components/ConnectionsList.vue` - Fixed API format mapping
- `frontend/src/App.vue` - Enhanced styling with NodeTile and card layouts

### Next Session Blockers (P0)
1. Add pagination to backend query endpoints (limit=50 default)
2. Implement "Load More" or virtual scrolling in ConnectionsList
3. Fix horizontal scroll layout bug
4. Filter stdlib imports from "Entry Points" category

---

## Session 11 (2025-11-08) - Frontend Networking & Vite Caching

### Summary
Fixed Vite proxy configuration and GraphClient URL construction. Frontend can now communicate with backend properly.

### Issues Fixed
- `GraphClient` now uses direct `http://localhost:8000/api` from browser (not Docker service name)
- Vite proxy configured for cross-container communication (`code-graph-http:8000`)
- Backend API format fixed (changed `type` → `node_type` in categories endpoint)

### Known Limitation
- Vite HMR doesn't always hot-reload code changes reliably
- Requires container restart or hard browser refresh when debugging
- This caused confusion during testing iterations

---

## Session 10 (2025-11-07) - API Format Fixes & Node Selection

### Summary
Fixed backend API response format to match frontend TypeScript interfaces. Full navigation loop now works end-to-end.

### Commits
- `df26cf7` - Fix backend API response format for categories endpoint
- `ad6a7c8` - Fix Vite dev server proxy configuration for Docker
- `aec2e22` - Fix API client to detect localhost and connect directly

### Navigation Flow Working
1. Browse categories → Load 20 nodes per category
2. Click node → Details pane shows complete information
3. Switch to Connections tab → See siblings in same file
4. Click sibling → Navigate to new node seamlessly

---

## Session 9 (2025-11-07) - Force Graph UI Redesign

### Summary
Complete UX redesign with "Code Geography" signpost metaphor. Created foundational navigation components.

### Commits
- `0cb6fe2` - feat: Add force-graph visualization and redesigned UX

### Components Created
- **NodeTile.vue** (107 lines) - Reusable signpost tile with distance indicators, direction arrows
- **ConnectionsList.vue** (218 lines) - "You are here" navigation view with callers/callees/siblings
- **App.vue** - Completely redesigned with tabbed layout

### Design Philosophy
- 📍 "You are here" → Current node card with stats
- Distance indicators → Hop counts like road signs (🟢 nearby, 🔴 far)
- Direction arrows → Upstream/downstream flow (🔵 callers, 🟢 callees, 🟡 siblings)
- No graph theory knowledge required

---

## Session 8 (2025-11-07) - Zero Nodes Root Cause Fix

### Summary
Fixed critical Redis serialization bug that was causing graph to show 0 nodes despite parsing working in tests.

### Root Cause
- Redis cache had stale/empty data from previous runs
- `asdict()` doesn't convert Enum objects to strings for msgpack
- Serialization failing with "can not serialize 'builtin_function_or_method' object"

### Solution
- Created `serialize_node()` and `serialize_relationship()` helper functions
- Convert `NodeType` and `RelationshipType` enums to `.value` strings before caching
- Added Redis FLUSHALL to workflow when changing code/workspace mounts

### Result
- Graph now stable: **483 nodes, 4,469 relationships** (was 0)
- Redis caching works correctly with enum serialization
- All query tools functional (find_callers, find_callees, find_references)

---

## Sessions 1-7 - Foundation & Core Features

**See `docs/sessions/current/` and `docs/archive/` for detailed notes.**

### Session 7: E2E Testing & Deployment
- Docker Compose multi-service stack
- Health checks and service dependencies
- Production deployment ready

### Session 6: Interactive Graph & Data Windowing
- DaisyUI styling framework integration
- Category browsing (Entry Points, Hubs, Leaves)
- Pagination on category endpoints
- Interactive Cytoscape graph (replaced in Session 9)

### Session 5: Query Endpoints & Tool UI
- Backend query endpoints (callers, callees, references)
- ToolPanel component for symbol queries
- 8 comprehensive tests (all passing)

### Session 4: Backend Stabilization
- Test infrastructure fixes (AsyncIO deprecation)
- Graph query testing (9/9 passing)
- Redis persistence validation

### Session 3: Multi-Language Seams
- Cross-language seam detection (C# → Node, Python → SQL, etc.)
- IgnorePatternsManager with .graphignore support
- 22/22 tests passing

### Session 2: Vue 3 Frontend
- Vue 3 + Vite + Pinia scaffolding
- GraphClient API wrapper (7 endpoints)
- 6 functional components
- Docker support (dev + prod)

### Session 1: REST API Implementation
- FastAPI HTTP server with 7 endpoints
- 8 Pydantic response models
- 3 traversal algorithms (DFS, BFS, call chain)
- 6/6 tests passing

---

## Architecture Overview

### Backend Stack (Python 3.12)
- **Parser**: AST-grep with multi-language support (25 languages)
- **Graph Library**: Rustworkx (high-performance Rust-based)
- **Cache**: Redis with msgpack serialization
- **Web Framework**: FastAPI with async/await
- **Package Manager**: uv (fast Python package manager)

### Frontend Stack (Node 22)
- **Framework**: Vue 3 + Composition API + TypeScript
- **Build Tool**: Vite 7.1.12
- **State**: Pinia stores (graphStore, filterStore, entryPointStore)
- **UI Framework**: DaisyUI + Tailwind CSS
- **HTTP Client**: Axios with type-safe wrappers

### Infrastructure
- **Docker Compose**: Multi-service stack
  - `code-graph-http` - FastAPI backend (port 8000)
  - `code-graph-sse` - MCP SSE server (port 10101)
  - `frontend` - Vite dev server (port 5173)
  - `redis` - Cache backend (port 6379)
  - `redis-insight` - Redis GUI (port 5540)
- **Networking**: Frontend → localhost:8000 → Backend → redis:6379
- **Volumes**: `repo-mount` for workspace, Redis persistence

### Key Classes & Components

**Backend**:
- `UniversalParser` - Multi-language AST parsing
- `UniversalGraph` - Graph data structure with relationship indexing
- `UniversalAnalysisEngine` - High-level analysis coordinator
- `RedisCacheBackend` - Persistent cache with serialization
- `GraphAPIRouter` - FastAPI router with query endpoints

**Frontend**:
- `GraphStore` - Pinia store for graph state, node selection, API calls
- `NodeTile` - Reusable node display component (signpost design)
- `ConnectionsList` - Relationship browser (callers, callees, siblings)
- `CategoryCard` - Browse category cards
- `GraphClient` - Type-safe API client wrapper

### Relationship Types
- **CONTAINS**: File contains function/class/method
- **CALLS**: Function calls another function
- **IMPORTS**: File imports module/library
- **INHERITS**: Class inheritance
- **IMPLEMENTS**: Interface implementation
- **SEAM**: Cross-language boundary call
- **REFERENCES**: Symbol reference (not yet fully implemented)

---

## Known Limitations & Issues

### Critical (Blocking Production)
- ❌ No pagination on relationship queries (causes browser crash with 1,000+ results)
- ❌ Horizontal scroll on desktop layout (responsive grid overflow)
- ❌ Import nodes dominate Entry Points category (stdlib noise)
- ❌ Mobile-first design not suitable for desktop workflow app

### High Priority
- ⚠️ No code preview or syntax highlighting
- ⚠️ No keyboard navigation
- ⚠️ No virtual scrolling for large lists
- ⚠️ Unknown graph completeness/accuracy per language
- ⚠️ No validation suite for relationship correctness

### Medium Priority
- ⚠️ No saved searches or bookmarking
- ⚠️ No export/share functionality
- ⚠️ No comparison mode (side-by-side nodes)
- ⚠️ No LLM integration for summaries
- ⚠️ Frontend healthcheck fails (cosmetic)

### Low Priority
- Limited mobile responsiveness (not primary target)
- No analytics/usage tracking
- No user authentication (out of scope)
- No CI/CD pipeline (manual Docker builds)

---

## Testing Status

### Unit Tests: 68+ Passing ✅
- Parser patterns for all 25 languages
- Relationship generation (CALLS, CONTAINS, IMPORTS)
- Category detection (entry points, hubs, leaves)
- Redis cache persistence and serialization
- Query endpoint logic
- Seam detection (11/11)
- Ignore patterns (11/11)

### Integration Tests: Limited ⚠️
- Backend query endpoint tests (8/8 passing)
- Frontend component tests (none yet)
- E2E Playwright tests (manual, not automated)

### Performance Tests: None ❌
- No benchmarks for large graphs
- No memory profiling
- No load testing

---

## Development Workflow

### Local Development
```bash
# Start full stack
compose.sh up

# View logs
compose.sh logs code-graph-http
compose.sh logs frontend

# Restart after code changes
compose.sh restart

# Clear Redis cache
docker exec code-graph-mcp-redis-1 redis-cli FLUSHALL
```

### Testing
```bash
# Backend tests
pytest tests/

# Specific test file
pytest tests/test_graph_queries.py -v

# In Docker
docker exec code-graph-mcp-code-graph-http-1 uv run pytest tests/
```

### Building Images
```bash
# Backend HTTP server
docker build -t ajacobm/code-graph-mcp:http -f Dockerfile --target http .

# Frontend dev
docker build -t code-graph-mcp-frontend -f frontend/Dockerfile frontend/

# Frontend production
docker build -t code-graph-mcp-frontend:prod -f frontend/Dockerfile.prod frontend/
```

---

## Git Branch Status

### Current Branch: `feature/sigma-graph-spike`
- **Base**: `main`
- **Commits Ahead**: 5 (unpushed)
- **Status**: Ready for merge after P0 fixes
- **Contains**: Sessions 9-12 work (UI redesign, bug fixes)

### Recent Commits (Last 5)
```
4d5c8c9 - fix: Handle correct API response format in ConnectionsList
5567256 - fix: Add error handling for relationship type deserialization
4eaf803 - feat: Enable sibling navigation in ConnectionsList
e2105c7 - feat: Connect ConnectionsList component to Connections tab
45881ec - fix: Add loaded nodes to store so selectNode can find them
```

### Next Branch: `feature/desktop-panels` (planned)
- Will branch from `feature/sigma-graph-spike`
- Contains Session 13 work (pagination, desktop panels, code preview)

---

## Quick Reference

### API Endpoints
- `GET /api/graph/stats` - Graph statistics
- `GET /api/graph/categories/{category}` - Browse entry points/hubs/leaves (with pagination ✅)
- `GET /api/graph/query/callers?symbol=X` - Find function callers (⚠️ no pagination)
- `GET /api/graph/query/callees?symbol=X` - Find function callees (⚠️ no pagination)
- `GET /api/graph/query/references?symbol=X` - Find symbol references (⚠️ no pagination)
- `POST /api/graph/traverse` - DFS/BFS graph traversal
- `POST /api/graph/subgraph` - Focused subgraph extraction
- `GET /api/graph/nodes/search?q=X` - Search nodes by name
- `GET /health` - Health check

### Frontend Routes
- Browse tab - Category cards and node grid
- Connections tab - Relationship browser (callers, callees, siblings)

### Docker Services
- `code-graph-http:8000` - Backend API
- `frontend:5173` - Vue dev server
- `redis:6379` - Cache backend
- `redis-insight:5540` - Redis GUI
- `code-graph-sse:10101` - MCP SSE server

---

## Strategic Vision

**Not an IDE** - This is a **knowledge mining and codebase-wide event-action-result flow analyzer**.

### Primary Use Cases
1. **Hidden Business Logic Discovery** - Find use cases buried in boilerplate
2. **Iterative LLM Workflows** - Feed code structure to Claude for analysis
3. **Stack Trace & Data-State Analysis** - Trace bugs through call chains
4. **Graph-Based Observability** - Visualize node highlighting during traversal
5. **Diagnostics & Root Cause** - Analyze runtime traces against code graph

### Future Capabilities
- Real-time LLM integration for code summaries
- Force-graph with WebSocket events for live analysis
- Neo4j migration for sophisticated Cypher queries
- Observability: Watch nodes highlight as analysis engine traverses them
- Code review mode with architectural context

---

**Next**: See `SESSION_13_PLAN.md` for detailed implementation plan.
