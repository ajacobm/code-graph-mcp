# CodeNavigator - Development Planning

**Last Updated**: 2025-11-08 | **Branch**: `feature/sigma-graph-spike` | **Commit**: `4d5c8c9`

---

## 🚨 Critical Blockers (P0) - Session 13

### Performance Crisis: 1,600+ Connections Rendering
**Problem**: Common import nodes (like Python's `re` module) have 1,123+ callers. The UI loads and renders ALL of them at once, causing browser timeout and sluggish performance.

**Evidence**:
- `re` import: 1,123 callers + 495 callees = 1,618 total connections
- All rendered as DOM nodes (no virtualization)
- Page screenshot timeout at 5000ms
- Tiny vertical scrollbar indicates massive list

**Required Fixes**:
1. **Backend Pagination** - Add `limit` and `offset` params to query endpoints:
   - `/api/graph/query/callers?symbol=X&limit=50&offset=0`
   - `/api/graph/query/callees?symbol=X&limit=50&offset=0`
   - `/api/graph/query/references?symbol=X&limit=50&offset=0`

2. **Frontend Progressive Disclosure**:
   - Show "First 50 of 1,123" with "Load More" button
   - Or implement virtual scrolling (vue-virtual-scroller)
   - Display total count prominently

3. **Import Node Filtering**:
   - Exclude stdlib imports (`re`, `asyncio`, `logging`, etc.) from "Entry Points" category
   - Or create separate "Library Imports" category
   - Focus entry points on actual application entry functions

### Desktop Layout Issues
**Problem**: UI designed mobile-first, not optimized for desktop workflow app.

**User Feedback**:
- "seems to be designed primarily for mobile"
- Horizontal scroll bar always present (slim edge cut off)
- Not suitable for knowledge mining workflow tool

**Required Fixes**:
1. Fix horizontal overflow in responsive grid layout
2. Redesign for desktop-first (multi-column, pinned panels)
3. Add code preview panel for desktop screens
4. Implement keyboard navigation

---

## 🎯 High Priority (P1) - Sessions 13-14

### Desktop Workflow App Redesign
**Vision**: Not an IDE, but a **knowledge mining and codebase-wide event-action-result flow analyzer**.

**Use Cases**:
- Hidden business logic discovery (find use cases in boilerplate)
- Iterative LLM workflows (feed code structure to Claude)
- Stack trace & data-state analysis
- Graph-based observability (visualize traversal/touches)
- Diagnostics & root cause analysis

**Desktop UI Requirements**:
1. **Multi-column layout** - Pinned sidebars, resizable panels
2. **Code preview** - Show actual code snippets on node selection
3. **Data table view** - Alternative to tiles for large datasets
4. **Keyboard shortcuts** - Navigate without mouse (arrow keys, Enter, Esc)
5. **Comparison mode** - Side-by-side node details
6. **Saved searches** - Bookmark interesting subgraphs
7. **Export/Share** - Generate URLs or JSON exports

### Graph Completeness Validation
**Problem**: Unknown if graph building is deterministic and complete across languages.

**Validation Strategy**:
1. **Create test modules** - Known call graphs in Python, TypeScript, C#
2. **Symbol counting tools** - Verify AST-grep matches expected counts
3. **Multi-parser comparison** - Compare AST-grep vs tree-sitter vs language-specific parsers
4. **Deterministic testing** - Run analysis multiple times, ensure identical results

**Questions to Answer**:
- Are we missing implicit calls (decorators, metaclasses, dynamic dispatch)?
- Do higher-order functions create correct relationships?
- What about async/await, generators, context managers?
- Cross-language seams: Are C# → Node.js calls detected?

---

## 🔮 Medium Priority (P2) - Sessions 15+

### Neo4j Migration Evaluation
**Question**: Is Redis → Neo4j worth the effort?

**Pros**:
- Native graph queries (Cypher) more powerful than custom traversal
- Built-in pattern matching and relationship analysis
- ACID compliance for consistency
- Visualization tools and query optimization
- Scales better for complex graph algorithms

**Cons**:
- Added infrastructure complexity
- Requires ETL pipeline (Redis → Neo4j)
- Learning curve for Cypher
- Resource overhead vs pure Redis cache

**Decision Point**: Evaluate after Python domain stabilized. Would enable sophisticated analysis impossible with Redis alone (e.g., "find all code paths from HTTP endpoint to database query").

### Force-Graph Observability
**Vision**: Real-time node highlighting during traversal or "touches"

**Implementation**:
- WebSocket connection for live graph events
- Highlight nodes as LLM or analysis engine traverses them
- Particle animations for data flow
- Timeline scrubber to replay analysis sessions

### LLM Integration Planning
**Workflows to Enable**:
1. Feed code structure to Claude for analysis
2. Generate architectural recommendations
3. Find business logic buried in boilerplate
4. Suggest refactoring opportunities based on graph patterns
5. Answer questions like "What happens when user clicks checkout?"

---

## 📊 Current State (Session 12)

### ✅ What's Working
- **Backend**: 974 nodes, 12,767 relationships, 25 language support
- **Relationship Queries**: find_callers returning 21+ results (was 0)
- **UI Navigation**: Browse → Select → Connections → Navigate flow
- **Styling**: Beautiful consistent design with NodeTile components
- **Docker Stack**: All services healthy, Redis caching operational

### 🐛 What's Broken
- **Performance**: Large result sets (1,600+ connections) crash browser
- **Desktop Layout**: Horizontal scroll, mobile-first responsive design
- **No Pagination**: API returns unlimited results
- **Import Noise**: Stdlib imports dominate "Entry Points" category

### 🔧 Recent Fixes (Session 12)
1. **Relationship Type Deserialization** - Fixed Redis cache enum conversion
2. **API Response Format** - Fixed callers/callees field mapping
3. **UI Styling** - NodeTile components, card layouts, consistent design
4. **Codegraph Integration** - Used for architecture analysis

---

## 🛠️ Technical Architecture

### Backend (Python)
- **Parser**: AST-grep with 25 language support
- **Graph**: Rustworkx (489 nodes, 4,475 relationships for core codebase)
- **Cache**: Redis with msgpack serialization
- **API**: FastAPI with async endpoints

### Frontend (Vue 3 + TypeScript)
- **Framework**: Vue 3 + Vite + Pinia
- **UI**: DaisyUI + Tailwind CSS
- **Components**: NodeTile, ConnectionsList, CategoryCard
- **API Client**: Axios with type-safe wrappers

### Infrastructure
- **Docker Compose**: Multi-service stack (HTTP, SSE, Redis, Frontend)
- **Networking**: Frontend localhost:5173 → Backend localhost:8000
- **Deployment**: Dev and prod Dockerfiles for each service

---

## 📈 Success Metrics

### Graph Quality
- [ ] 95%+ relationship accuracy for Python (vs manual validation)
- [ ] Deterministic analysis (same results across runs)
- [ ] Support for implicit calls (decorators, async, etc.)
- [ ] Cross-language seam detection working

### User Experience
- [ ] Handle 10,000+ node graphs without lag
- [ ] Desktop-optimized layout with multi-column views
- [ ] Code preview on hover/selection
- [ ] Keyboard navigation throughout

### Developer Experience
- [ ] Clear documentation for new contributors
- [ ] Comprehensive test coverage (unit + integration)
- [ ] Easy local development setup
- [ ] CI/CD pipeline for automated testing

---

## 🗺️ Roadmap

### Session 13: Performance & Pagination
1. Add limit/offset to backend query endpoints
2. Implement "Load More" in ConnectionsList
3. Fix horizontal scroll layout bug
4. Filter stdlib imports from categories

### Session 14: Desktop Redesign
1. Multi-column layout with pinned panels
2. Code preview panel integration
3. Keyboard navigation implementation
4. Data table view for large lists

### Session 15: Graph Validation
1. Create Python test suite with known call graphs
2. Implement symbol counting validation tools
3. Test TypeScript and C# support
4. Document relationship accuracy metrics

### Session 16+: Advanced Features
1. Neo4j migration spike
2. Force-graph visualization with WebSocket events
3. LLM integration for code analysis
4. Saved searches and bookmarking
5. Export/share functionality

---

## 🧪 Testing Strategy

### Unit Tests (68+ passing)
- Parser patterns for all languages
- Relationship generation (CALLS, CONTAINS, IMPORTS)
- Category detection (entry points, hubs, leaves)
- Redis cache persistence

### Integration Tests
- End-to-end API flows
- Frontend component interactions
- Docker stack deployment

### Validation Tests (TODO)
- Known call graph comparison
- Symbol count verification
- Multi-parser accuracy comparison
- Performance benchmarks

---

## 🤔 Open Questions

1. **Graph Completeness**: How do we measure if we're capturing all relationships?
2. **Import Filtering**: Should we exclude all stdlib imports or just from certain views?
3. **Pagination Strategy**: Virtual scrolling vs "Load More" vs traditional pagination?
4. **Neo4j Migration**: Worth the complexity for Cypher query power?
5. **Desktop vs Mobile**: Build separate UIs or one responsive design?

---

## 📝 Notes for Future Sessions

- Cortexgraph MCP is excellent for session continuity (8 memories saved Session 12)
- Codegraph MCP useful for architecture insights (circular deps, critical nodes)
- Always test with high-degree nodes like `re` to catch performance issues
- Playwright essential for real UX validation
- Trust rustworkx - focus on AST-grep pattern accuracy, not graph library bugs
