# Documentation Index

Welcome to the Code Graph MCP documentation. This index helps you navigate the project's knowledge base.

## 📋 Quick Navigation

- **[Technical Specifications](#technical-specifications)** - Design decisions, architecture, and technical specs
- **[Guides & Tutorials](#guides--tutorials)** - How-to guides, setup instructions, and troubleshooting
- **[Session Records](#session-records)** - Development progress and decision logs
- **[Archive](#archive)** - Historical documents and previous iterations

---

## 📐 Technical Specifications

Core technical documentation for the project's design and architecture.

| Spec | Purpose | Status |
|------|---------|--------|
| **[DOTNET_INTEGRATION.md](specs/DOTNET_INTEGRATION.md)** | OpenAPI 3.1 spec generation and NSwag C# client integration | ✅ Complete |
| **[GRAPH_DATABASE_EVALUATION.md](specs/GRAPH_DATABASE_EVALUATION.md)** | Memgraph vs. Neo4j evaluation and selection rationale | ✅ Complete |
| **[BACKEND_HOSTING_GUIDE.md](specs/BACKEND_HOSTING_GUIDE.md)** | HTTP API deployment and infrastructure specifications | ✅ Complete |
| **[FRONTEND_DEPLOYMENT.md](specs/FRONTEND_DEPLOYMENT.md)** | Frontend build, deployment, and CDN integration | ✅ Complete |
| **[MCP_AGENT_INTEGRATION.md](specs/MCP_AGENT_INTEGRATION.md)** | Model Context Protocol agent tool integration | ✅ Complete |
| **[ENTRY_POINT_DISCOVERY.md](specs/ENTRY_POINT_DISCOVERY.md)** | Entry point detection algorithms and implementation | ✅ Complete |

---

## 📚 Guides & Tutorials

Step-by-step guides and how-to documentation for common tasks.

| Guide | Purpose | Audience |
|-------|---------|----------|
| **[CODESPACES_INFRASTRUCTURE.md](guides/CODESPACES_INFRASTRUCTURE.md)** | GitHub Codespaces setup and configuration | DevOps / Contributors |
| **[CODESPACES_TROUBLESHOOTING.md](guides/CODESPACES_TROUBLESHOOTING.md)** | Debugging Codespaces issues | Contributors |
| **[PLAYWRIGHT_TESTING_GUIDE.md](guides/PLAYWRIGHT_TESTING_GUIDE.md)** | E2E testing with Playwright | QA / Contributors |
| **[TESTING_GUIDE.md](guides/TESTING_GUIDE.md)** | Unit and integration testing strategies | Developers |
| **[FRONTEND_ENHANCEMENT.md](guides/FRONTEND_ENHANCEMENT.md)** | Frontend feature development workflow | Frontend Developers |
| **[REDESIGN_PROPOSAL.md](guides/REDESIGN_PROPOSAL.md)** | UI/UX redesign concepts and mobile-first approach | UI/UX Team |

---

## 📖 Session Records

Development progress tracked by session. Sessions are listed chronologically from oldest to newest.

### Active Development Sessions

These sessions document the current feature implementation cycle:

- **[SESSION_15_COMPLETION.md](sessions/SESSION_15_COMPLETION.md)** - Session 15 completion summary
- **[SESSION_13_PLAN.md](sessions/SESSION_13_PLAN.md)** - Session 13 planning documentation

### Infrastructure & Core Features

Early sessions establishing the project foundation:

- Earlier session documentation available in `/docs/sessions/`

---

## 🗂️ Archive

Historical documents and superseded specifications. Use these for reference only.

| Document | Purpose |
|----------|---------|
| **[CURRENT_STATE.md](../CURRENT_STATE.md)** | Project snapshot (root level) |
| **[PLANNING.md](../PLANNING.md)** | Long-term planning (root level) |
| **[CRUSH.md](../CRUSH.md)** | Known issues and technical debt (root level) |

Older archived documentation available in `/docs/archive/`.

---

## 🎯 Key Project Components

### Infrastructure
- **Docker Compose**: Multi-container setup (Redis, Memgraph, Backend API, Jupyter)
- **CDC Sync Worker**: Real-time code graph synchronization
- **Query Router**: Complexity-based query optimization

### Analysis (Jupyter Notebooks)
The `/notebooks/` directory contains interactive analysis:
1. **01_graph_basics.ipynb** - Graph fundamentals and connection setup
2. **02_centrality_analysis.ipynb** - Critical function identification
3. **03_community_detection.ipynb** - Module boundary detection
4. **04_architectural_patterns.ipynb** - Code smell detection and scoring
5. **05_ontology_extraction.ipynb** - Domain vocabulary and semantic modeling
6. **06_c4_diagram_generation.ipynb** - Architecture visualization

### Testing
- **Unit Tests**: `/tests/` directory
- **E2E Tests**: `/tests/playwright/` (with Playwright framework)
- **Integration Tests**: Service-level testing via HTTP API

---

## 🔄 Development Workflow

1. **Plan** → Review specs in `/specs/` for design decisions
2. **Setup** → Follow guides in `/guides/` for environment configuration
3. **Develop** → Implement features following established patterns
4. **Test** → Use testing guides in `/guides/`
5. **Document** → Add session notes to `/sessions/`

---

## 🤝 Contributing

- **First time setup?** Start with [CODESPACES_INFRASTRUCTURE.md](guides/CODESPACES_INFRASTRUCTURE.md)
- **Writing tests?** See [TESTING_GUIDE.md](guides/TESTING_GUIDE.md)
- **E2E testing?** Reference [PLAYWRIGHT_TESTING_GUIDE.md](guides/PLAYWRIGHT_TESTING_GUIDE.md)
- **Architecture questions?** Check `/specs/` directory for design rationale
- **Debugging issues?** See [CODESPACES_TROUBLESHOOTING.md](guides/CODESPACES_TROUBLESHOOTING.md)

---

## 📊 Project Statistics

- **Total Nodes (Graph)**: 489+
- **Total Edges (Graph)**: 4,475+
- **Supported Languages**: Python, TypeScript, JavaScript, Go (expandable)
- **Test Coverage**: Increasing (unit, integration, E2E)
- **Documentation**: Organized by purpose (specs, guides, sessions)

---

## 🚀 Getting Started Checklist

- [ ] Clone the repository
- [ ] Run `docker-compose up` to start services (see [CODESPACES_INFRASTRUCTURE.md](guides/CODESPACES_INFRASTRUCTURE.md))
- [ ] Access Jupyter notebooks for analysis at `http://localhost:8888`
- [ ] Review [BACKEND_HOSTING_GUIDE.md](specs/BACKEND_HOSTING_GUIDE.md) for API details
- [ ] Start with Notebook 01 to understand the graph structure
- [ ] Join development sessions (see `/sessions/` for recent notes)

---

**Last Updated**: November 15, 2025  
**Branch**: feature/memgraph-integration  
**Maintained By**: Development Team

