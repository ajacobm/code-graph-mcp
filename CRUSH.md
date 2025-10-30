# Crush Session Memory

## Bash Session Init
Always initialize sessions with: `source ~/.bashrc`

## Docker Commands
- View logs: `docker logs code-graph-mcp-code-graph-codegraphmcp-sse-1`
- List running containers: `docker ps -a | grep code-graph`
- Restart stack: `docker-compose -f docker-compose-multi.yml down && docker-compose -f docker-compose-multi.yml up -d`

## Development Commands
- Run tests: `pytest tests/`
- Type check: `mypy src/`
- Lint: `ruff check src/`
- Build Docker: `docker build -t ajacobm/code-graph-mcp:sse -f Dockerfile .`

## Workspace Setup
The `/app/workspace` volume in Docker is mounted from `repo-mount` volume (empty by default).
To analyze code:
1. Mount a real repo to the volume in docker-compose-multi.yml, or
2. Clone a repo into the volume from container startup

## Key Architecture Notes
- `UniversalAnalysisEngine` has `analyzer` (UniversalASTAnalyzer) which holds the `cache_manager`
- Property added to `UniversalAnalysisEngine.cache_manager` for safe access
- SSE server uses `StreamableHTTPSessionManager` from official MCP SDK
- Health check endpoint at `/health` safely checks Redis connectivity
- File watcher: `get_supported_extensions()` is async, must be awaited in `start_file_watcher()`
- MCP handlers: Added `list_prompts()` and `list_resources()` handlers to prevent "Method not found" errors

## Recent Fixes (2025-10-25)
1. Fixed `cache_manager` AttributeError in health checks - added property delegation
2. Fixed file watcher coroutine not awaited - now properly awaits `get_supported_extensions()`
3. Added missing MCP protocol handlers for prompts and resources
4. All tools (get_usage_guide, analyze_codebase) now execute without errors

## Graph Query Tools - Zero Results Fix (2025-10-30)
**Problem**: find_references, find_callers, find_callees returned zero results
**Root Cause**: Parser created CONTAINS/IMPORTS relationships but not CALLS relationships
**Solution**: 
- Enhanced UniversalParser with _extract_function_calls_ast() method
- Added "call" AST patterns for all 25+ languages
- Created 5560+ CALLS relationships across codebase
**Results**: 
- find_callers now returns 85+ results (vs 0)
- find_callees now returns 29+ results (vs 0)
- All query tools working correctly

**Test commands**:
```bash
docker run --rm -v /path/to/code-graph-mcp:/app code-graph-mcp:test uv run python /app/tests/test_calls_implementation.py
docker run --rm -v /path/to/code-graph-mcp:/app code-graph-mcp:test uv run python /app/tests/test_query_tools_live.py
docker run --rm -v /path/to/code-graph-mcp:/app code-graph-mcp:test uv run python /app/tests/test_mcp_live_session.py
```

## Multi-Language Seams & Ignore Patterns (2025-10-29)
**Feature**: Cross-language seam detection and ignore pattern management
**Files Added**:
- `src/code_graph_mcp/ignore_patterns.py` - IgnorePatternsManager (reads .graphignore)
- `src/code_graph_mcp/seam_detector.py` - SeamDetector (detects C#->Node, Python->SQL, etc)
- `tests/test_ignore_patterns.py` - 11 tests for pattern matching
- `tests/test_seam_detector.py` - 11 tests for cross-language detection
- `.graphignore.example` - template for ignore patterns

**Key Classes**:
- `IgnorePatternsManager`: Load from .graphignore, filter paths/languages
- `SeamDetector`: Identify cross-language calls with regex patterns
- `RelationshipType.SEAM`: New graph relationship type

**Registered Seams** (auto-detected):
- C# → Node.js (HttpClient, PostAsync)
- C# → SQL (SqlConnection, SqlCommand)
- TypeScript → Python (fetch, axios, api)
- TypeScript → Node (import, require, @nestjs, express)
- Python → Java (subprocess, socket, grpc)
- Python → SQL (sqlite3, psycopg2, execute)

**Test coverage**: 22/22 tests passing
- Pattern matching with wildcards, includes, language filters
- Seam detection in multi-language code
- Runtime pattern/language addition

## Session 2: Vue3 Frontend (2025-10-30)
**Status**: ✅ Complete + Dockerized
**Files**: 31 new (6 components, 2 stores, 3 API/types, 4 config, 4 docs, 2 Dockerfiles, 1 script)
**Lines**: ~1400 new

**Key Deliverables**:
- Vue 3 + Vite full project scaffold
- GraphClient API wrapper (all 7 endpoints)
- 6 fully functional components (GraphViewer, NodeDetails, SearchBar, FilterPanel, CallChainTracer, LoadingSpinner)
- Pinia stores with real-time filtering (language, type, complexity, search, seams)
- Cytoscape.js graph rendering with DAG layout + hover/select effects
- Dark theme UX (indigo/pink/gray palette)
- Responsive layout (header + sidebars + graph)
- DEV_GUIDE.md + README.md + DOCKER.md complete
- start-dev.sh for integrated testing
- ✅ **Docker support** (Dockerfile dev + Dockerfile.prod)
- ✅ **Docker Compose integration** (full stack in one command)

**Solved**: Node version issue with containerization
- Dockerfile uses Node 22-alpine (fixes Vite requirements)
- No nvm needed on host
- Full reproducible environment
- docker-compose-multi.yml includes frontend service

**Branch**: `feature/graph-ui-vue`
**Commits**: 6 (scaffolding, enhancements, final, Docker)

## Next Steps (Session 3)
1. ✅ Session 1: REST API + graph traversal (DONE)
2. ✅ Session 2: Vue3 UI with Cytoscape visualization (DONE)
3. 📋 Session 3: DuckDB integration, tagging, graph comparison
