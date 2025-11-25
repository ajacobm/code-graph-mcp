# Getting Started - Code Graph Visualizer

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Vue 3 + Vite)                  │
│               http://localhost:5173                         │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐    │
│  │  GraphViewer │  │ NodeDetails  │  │   FilterPanel  │    │
│  │ (Cytoscape)  │  │  (Sidebar)   │  │   (Sidebar)    │    │
│  └──────────────┘  └──────────────┘  └────────────────┘    │
│        ▲                                                    │
│        │ API Calls (/api/graph/*)                          │
│        ▼                                                    │
├─────────────────────────────────────────────────────────────┤
│                Backend (FastAPI + Uvicorn)                  │
│               http://localhost:8000                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │       UniversalAnalysisEngine                        │   │
│  │   (AST Analysis + Code Graph Building)              │   │
│  │   ┌──────────────────────────────────────┐          │   │
│  │   │  RustworkxCodeGraph (Graph Database) │          │   │
│  │   │  - 367 nodes, 1907 relationships     │          │   │
│  │   │  - 25+ languages supported           │          │   │
│  │   │  - SEAM detection (cross-language)   │          │   │
│  │   └──────────────────────────────────────┘          │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start (Recommended: Docker)

**One Command - Everything:**
```bash
docker-compose -f docker-compose-multi.yml up
```

Then open: **http://localhost:5173**

Services will be ready in ~15 seconds:
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- Redis: localhost:6379
- Redis Insight: http://localhost:5540

---

## Quick Start (Local Development)

### 1. Start Backend

```bash
python -m codenav.http_server --host 0.0.0.0 --port 8000
```

**Wait for**: `Application startup complete`

### 2. Start Frontend (Docker)

**IMPORTANT**: Your system has Node 18.19.1, but Vite needs Node 20+. Use Docker:

```bash
docker build -f frontend/Dockerfile -t code-graph-frontend:dev .
docker run -it --rm \
  -p 5173:5173 \
  -v $(pwd)/frontend:/app \
  -v /app/node_modules \
  code-graph-frontend:dev
```

Or use Docker Compose for both:
```bash
docker-compose -f docker-compose-multi.yml up
```

### 3. Open Browser

Navigate to: **http://localhost:5173**

## Usage Guide

### Basic Workflow

1. **Load Graph**: Enter a node ID (e.g., from top functions list) and click "Traverse"
2. **View Node**: Click any node in the graph to see details on the right
3. **Filter**: Click "Show Filters" to reduce nodes by language/type/complexity
4. **Search**: Use search bar to find specific nodes
5. **Call Chain**: Click "Call Chain" to trace linear call paths

### Features

#### Graph Visualization
- Click nodes to select
- Hover for visual feedback
- Pan with mouse drag
- Zoom with mouse wheel
- Right-click to context menu

#### Node Details Panel (Right)
- Full node metadata
- Shows callers (incoming edges)
- Shows callees (outgoing edges)
- Click related nodes to navigate

#### Filtering (Left Sidebar)
- **Languages**: Filter by programming language
- **Types**: Filter by node type (function, class, etc.)
- **Complexity**: Adjust range slider
- **SEAM Only**: Show only cross-language relationships

#### Search
- Autocomplete as you type
- Shows language badge
- Click to load that node

## API Endpoints

The frontend uses these REST API endpoints:

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/api/graph/stats` | Get total nodes/relationships |
| `GET` | `/api/graph/nodes/{id}` | Get single node details |
| `POST` | `/api/graph/traverse` | Traverse DFS/BFS from node |
| `GET` | `/api/graph/nodes/search` | Search nodes by name |
| `GET` | `/api/graph/seams` | Get all SEAM relationships |
| `GET` | `/api/graph/call-chain/{id}` | Get linear call sequence |

## Project Structure

```
codenav/
├── src/                           # Python backend
│   └── codenav/
│       ├── http_server.py         # FastAPI entry point
│       ├── universal_parser.py    # AST parsing (25+ languages)
│       ├── universal_graph.py     # Graph data structure
│       ├── server/
│       │   ├── graph_api.py       # REST endpoints
│       │   └── analysis_engine.py # Core analyzer
│       └── graph/
│           ├── traversal.py       # DFS/BFS algorithms
│           └── query_response.py  # Response DTOs
│
├── frontend/                      # Vue 3 + Vite
│   ├── src/
│   │   ├── components/            # 6 Vue components
│   │   ├── api/graphClient.ts     # Axios wrapper
│   │   ├── stores/                # Pinia state
│   │   └── types/graph.ts         # TypeScript interfaces
│   ├── vite.config.ts             # Proxy to :8000
│   └── package.json               # Dependencies
│
└── tests/                         # Python unit tests
```

## Development

### Frontend Development

```bash
cd frontend

# Start dev server with hot reload
npm run dev

# Type check
npm run type-check

# Build for production
npm run build

# Preview production build
npm run preview
```

See `frontend/DEV_GUIDE.md` for detailed Vue/Vite instructions.

### Backend Development

```bash
# Run tests
pytest tests/

# Type check
mypy src/

# Lint
ruff check src/

# Run HTTP server
python -m codenav.http_server --help
```

## Troubleshooting

### Frontend Won't Start

**Error**: `crypto.hash is not a function`
- **Cause**: Node 18.x, Vite needs 20+
- **Fix**: Upgrade Node or use Node 20+ environment

**Error**: `Port 5173 already in use`
- Vite will use next available port
- Check terminal output for actual port

### API Connection Failed

**Error**: `Failed to load stats` (in UI)
- Make sure backend is running on `:8000`
- Check browser console for actual error
- Verify CORS is enabled (it is by default)

### Graph Not Rendering

**Empty Graph**: Enter a node ID and click Traverse
- Start with node from "Top Functions" in stats

**Nodes but No Edges**: May need to increase depth
- Default depth is 5, try 10 for more relationships

## Performance Tips

- **Large Graphs** (1000+ nodes): Use filters to reduce visible nodes
- **Slow Traversal**: Increase depth gradually (default 5)
- **Layout Issues**: Pan out and fit (graph auto-fits on load)

## Architecture Notes

### Frontend (Vue 3)
- **State**: Pinia stores (graphStore, filterStore)
- **Reactivity**: Computed properties for filtered arrays
- **Visualization**: Cytoscape.js with Dagre layout
- **API**: Typed Axios client

### Backend (FastAPI)
- **Analysis**: Universal AST parser (25+ languages)
- **Graph**: Rustworkx (high-performance)
- **Caching**: Optional Redis
- **Relationships**: CONTAINS, IMPORTS, CALLS, SEAM

## Key Technologies

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | Vue 3 | Component framework |
| | Vite | Fast dev server |
| | Cytoscape.js | Graph rendering |
| | Pinia | State management |
| Backend | FastAPI | REST API |
| | Rustworkx | Graph database |
| | ast-grep | Code parsing |

## Next Steps

1. **Explore Graph**: Try different nodes and traversals
2. **Analyze Code**: Use filters to find patterns
3. **Export Data**: Call chain can be exported as JSON
4. **Session 3**: DuckDB integration for advanced analytics

## Help & Documentation

- `frontend/DEV_GUIDE.md` - Frontend development guide
- `frontend/README.md` - Feature overview
- `docs/sessions/current/SESSION_2_FRONTEND.md` - Session report
- `CRUSH.md` - Development notes

## Support

All code is tested and documented. If you encounter issues:

1. Check the browser console (F12) for errors
2. Check backend logs for API errors
3. Ensure both services are running on correct ports
4. Review the DEV_GUIDE for your specific environment
