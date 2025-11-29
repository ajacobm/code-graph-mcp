# CodeNavigator Agent Team

This directory contains specialized AI agents for the CodeNavigator (codenav) project. Each agent is designed to excel in a specific domain and work collaboratively to deliver high-quality software.

## Overview

The agent team is organized to cover all aspects of software development, from planning to deployment:

```
┌─────────────────────────────────────────────────────────────────┐
│                     Team Coordinator                             │
│                  Orchestrates all agents                         │
└─────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐       ┌───────────────┐       ┌───────────────┐
│   Solution    │       │    Backend    │       │   Frontend    │
│   Architect   │       │   Engineer    │       │   Engineer    │
│               │       │   (Python)    │       │ (React/TS)    │
└───────────────┘       └───────────────┘       └───────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐       ┌───────────────┐       ┌───────────────┐
│     Code      │       │      QA       │       │    Coding     │
│   Reviewer    │◄──────│   Engineer    │───────►   Standards   │
│               │       │               │       │               │
└───────────────┘       └───────────────┘       └───────────────┘
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                │
        ┌───────────────────────┴───────────────────────┐
        │                                               │
        ▼                                               ▼
┌───────────────┐                               ┌───────────────┐
│    Kanban     │                               │    DevOps     │
│   Manager     │                               │   Engineer    │
│               │                               │               │
└───────────────┘                               └───────────────┘
```

## Agents

### 🏗️ [Solution Architect](solution-architect.md)
**Role**: High-level architectural decisions, technical planning, system design
- Creates technical designs and ADRs
- Ensures architectural consistency
- Plans feature implementations
- Reviews system design

### 🐍 [Backend Engineer](backend-engineer.md)
**Role**: Python backend development, MCP server, code analysis engine
- Implements AST parsing and graph building
- Develops MCP tools and handlers
- Optimizes performance and caching
- Maintains API endpoints

### ⚛️ [Frontend Engineer](frontend-engineer.md)
**Role**: React/TypeScript UI, graph visualization, user experience
- Builds React components
- Implements force-graph visualization
- Manages state with Zustand
- Integrates with backend APIs

### 👀 [Code Reviewer](code-reviewer.md)
**Role**: Code quality reviews, security checks, best practices enforcement
- Reviews all code changes
- Ensures quality standards
- Catches bugs and security issues
- Provides constructive feedback

### 🧪 [QA Engineer](qa-engineer.md)
**Role**: Testing strategy, test implementation, validation
- Writes and maintains tests
- Creates test plans
- Validates features
- Tracks quality metrics

### 📐 [Coding Standards](coding-standards.md)
**Role**: Style enforcement, conventions, code consistency
- Enforces Python (Ruff/Black) standards
- Enforces TypeScript (ESLint) standards
- Maintains naming conventions
- Ensures documentation quality

### 🎯 [Team Coordinator](team-coordinator.md)
**Role**: Workflow orchestration, task delegation, collaboration
- Assigns tasks to agents
- Manages handoffs
- Resolves blockers
- Tracks overall progress

### 📋 [Kanban Manager](kanban-manager.md)
**Role**: Project board management, issue tracking, sprint planning
- Manages GitHub Projects board
- Triages issues
- Tracks sprint progress
- Maintains project visibility

### 🐳 [DevOps Engineer](devops-engineer.md)
**Role**: CI/CD, Docker infrastructure, deployment, monitoring
- Maintains GitHub Actions workflows
- Manages Docker configurations
- Handles deployments
- Ensures reliability

## Usage

Each agent can be invoked to assist with tasks in their domain. Reference the specific agent file for:
- Detailed responsibilities
- Technical standards
- Common tasks
- Code examples
- Best practices

## Workflow

### Feature Development
1. **Solution Architect** creates technical design
2. **Team Coordinator** assigns to appropriate engineer
3. **Backend/Frontend Engineer** implements feature
4. **Coding Standards** reviews code style
5. **Code Reviewer** reviews implementation
6. **QA Engineer** validates functionality
7. **Kanban Manager** updates board status
8. **DevOps Engineer** handles deployment

### Bug Fixing
1. **Kanban Manager** triages and prioritizes
2. **Team Coordinator** assigns to engineer
3. **Backend/Frontend Engineer** fixes bug
4. **Code Reviewer** reviews fix
5. **QA Engineer** verifies fix
6. **Kanban Manager** closes issue

## Project Context

CodeNavigator is an MCP server providing code analysis across 25+ programming languages:

- **Backend**: Python 3.12+, FastAPI, AST-grep, rustworkx, Redis
- **Frontend**: React 19, TypeScript, force-graph, Zustand
- **Infrastructure**: Docker Compose, GitHub Actions, GHCR

Key directories:
- `/src/codenav/` - Python backend
- `/frontend/` - React frontend
- `/infrastructure/` - Docker configs
- `/tests/` - Test files
- `/docs/` - Documentation

## Contributing

When adding or modifying agents:
1. Follow the existing agent file format
2. Include clear responsibilities
3. Provide code examples
4. Reference relevant project files
5. Update this README if needed
