# CodeNavigator Frontend

Force-directed graph visualization for CodeNavigator, built with React 19, TypeScript, and Zustand.

## Tech Stack

As recommended in the [GRAPH_VISUALIZATION_PLAN.md](../docs/GRAPH_VISUALIZATION_PLAN.md):

- **React 19** - Frontend framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Zustand** - State management
- **Tailwind CSS** - Styling
- **force-graph** - Graph visualization library
- **Radix UI** - Accessible UI primitives

## Getting Started

### Prerequisites

- Node.js 18+
- npm 9+
- Backend HTTP API running on http://localhost:10102

### Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The app will be available at http://localhost:5173

### Production Build

```bash
npm run build
npm run preview
```

## Architecture

```
frontend/
├── src/
│   ├── components/
│   │   ├── graph/           # ForceGraph, GraphControls, NodeTooltip
│   │   ├── panels/          # ToolsPanel, DetailsPanel
│   │   └── layout/          # Header, StatusBar
│   ├── hooks/               # React hooks
│   ├── stores/              # Zustand stores
│   │   └── graphStore.ts    # Graph state management
│   ├── api/                 # API client
│   │   └── graphApi.ts      # HTTP calls to backend
│   ├── types/               # TypeScript types
│   │   └── index.ts         # Shared type definitions
│   ├── App.tsx              # Main application
│   ├── main.tsx             # Entry point
│   └── index.css            # Global styles + Tailwind
├── public/
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── tsconfig.json
```

## Features

### Implemented

- ✅ Force-directed graph visualization
- ✅ Node selection and details panel
- ✅ Color by type/language/complexity
- ✅ Node search with highlighting
- ✅ Zoom to fit / center on node
- ✅ Collapsible side panels
- ✅ Live stats display
- ✅ Re-analyze trigger

### Planned

- 🔜 WebSocket integration for real-time updates
- 🔜 Pathway visualization
- 🔜 Annotation system
- 🔜 Cluster detection
- 🔜 Export/share functionality

## API Integration

The frontend connects to the backend API at `/api/graph/*`:

- `GET /api/graph/export` - Full graph data for visualization
- `GET /api/graph/stats` - Graph statistics
- `GET /api/graph/categories/:category` - Node categories
- `GET /api/graph/nodes/search` - Node search
- `POST /api/graph/admin/reanalyze` - Force re-analysis

## Styling

Using Tailwind CSS with a dark slate color scheme. The color palette:

- Background: `slate-900`
- Panels: `slate-800`
- Borders: `slate-700`
- Text: `slate-100` to `slate-400`
- Accent: `indigo-600`
- Success: `green-500`
- Warning: `amber-500`
- Error: `red-500`

## Related

- [GRAPH_VISUALIZATION_PLAN.md](../docs/GRAPH_VISUALIZATION_PLAN.md) - Feature planning document
- [Backend API](../src/codenav/) - Python FastAPI backend
