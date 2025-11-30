.PHONY: help dev-up dev-down dev-logs backend-up backend-down codespaces-up codespaces-down ghcr-up ghcr-down clean rebuild lint test

# Docker Compose configurations
COMPOSE_BASE := docker-compose -f infrastructure/docker-compose.yml
COMPOSE_BACKEND := $(COMPOSE_BASE) -f infrastructure/profiles/backend-only.yml
COMPOSE_CODESPACES := $(COMPOSE_BASE) -f infrastructure/profiles/codespaces.yml
COMPOSE_GHCR := $(COMPOSE_BASE) -f infrastructure/profiles/ghcr.yml

help:
	@echo "CodeNavigator (codenav) - Make Targets"
	@echo ""
	@echo "Docker Compose Stacks:"
	@echo "  make dev-up           - Full development stack (Redis, Memgraph, API, Jupyter, Frontend)"
	@echo "  make dev-down         - Stop development stack"
	@echo "  make dev-logs         - View development logs"
	@echo "  make dev-status       - Show container status"
	@echo ""
	@echo "  make backend-up       - Backend only (for local frontend dev with npm)"
	@echo "  make backend-down     - Stop backend services"
	@echo ""
	@echo "  make codespaces-up    - Codespaces stack (builds from source, includes frontend)"
	@echo "  make codespaces-down  - Stop Codespaces stack"
	@echo ""
	@echo "  make ghcr-up          - GHCR images (pre-built production test)"
	@echo "  make ghcr-down        - Stop GHCR stack"
	@echo ""
	@echo "Infrastructure:"
	@echo "  make clean            - Remove all containers and volumes"
	@echo "  make rebuild          - Rebuild all images"
	@echo "  make ps               - Show running containers"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint             - Run linting checks"
	@echo "  make format           - Format Python code"
	@echo ""
	@echo "Testing:"
	@echo "  make test             - Run pytest suite"
	@echo "  make test-coverage    - Run pytest with coverage"
	@echo ""

# =============================================================================
# Full Development Stack (all services)
# =============================================================================

dev-up:
	$(COMPOSE_BASE) up -d
	@echo "✅ Full development stack started"
	@echo "   - Redis:     localhost:6379"
	@echo "   - SSE/MCP:   localhost:10101"
	@echo "   - HTTP API:  localhost:10102"
	@echo "   - Frontend:  localhost:5173"
	@echo "   - Memgraph:  localhost:7687 (Lab: localhost:3000)"
	@echo "   - Jupyter:   localhost:8888"

dev-down:
	$(COMPOSE_BASE) down
	@echo "✅ Development stack stopped"

dev-logs:
	$(COMPOSE_BASE) logs -f

dev-status:
	$(COMPOSE_BASE) ps

dev-shell:
	$(COMPOSE_BASE) exec codenav-web bash

# With monitoring (Redis Insight)
dev-monitoring:
	$(COMPOSE_BASE) --profile monitoring up -d
	@echo "✅ Development stack with monitoring started"
	@echo "   - Redis Insight: localhost:5540"

# =============================================================================
# Backend Only (for local frontend development)
# =============================================================================

backend-up:
	$(COMPOSE_BACKEND) up -d
	@echo "✅ Backend services started"
	@echo "   Run frontend locally: cd frontend && npm run dev"

backend-down:
	$(COMPOSE_BACKEND) down
	@echo "✅ Backend services stopped"

backend-logs:
	$(COMPOSE_BACKEND) logs -f

# =============================================================================
# GitHub Codespaces
# =============================================================================

codespaces-up:
	$(COMPOSE_CODESPACES) up -d --build
	@echo "✅ Codespaces stack started"

codespaces-down:
	$(COMPOSE_CODESPACES) down
	@echo "✅ Codespaces stack stopped"

codespaces-logs:
	$(COMPOSE_CODESPACES) logs -f

# =============================================================================
# GHCR Pre-built Images
# =============================================================================

ghcr-up:
	$(COMPOSE_GHCR) up -d
	@echo "✅ GHCR stack started (using pre-built images)"

ghcr-down:
	$(COMPOSE_GHCR) down
	@echo "✅ GHCR stack stopped"

ghcr-logs:
	$(COMPOSE_GHCR) logs -f

ghcr-pull:
	$(COMPOSE_GHCR) pull
	@echo "✅ GHCR images pulled"

# =============================================================================
# Infrastructure Management
# =============================================================================

clean:
	$(COMPOSE_BASE) down -v --remove-orphans
	@echo "✅ All containers and volumes removed"

rebuild:
	$(COMPOSE_BASE) build --no-cache
	@echo "✅ All images rebuilt"

ps:
	$(COMPOSE_BASE) ps

# =============================================================================
# Code Quality
# =============================================================================

lint:
	uv run ruff check src/ tests/
	@echo "✅ Linting complete"

format:
	uv run ruff format src/ tests/
	@echo "✅ Code formatted"

# =============================================================================
# Testing
# =============================================================================

test:
	uv run pytest tests/ -v

test-coverage:
	uv run pytest tests/ --cov=src --cov-report=html
	@echo "✅ Coverage report: htmlcov/index.html"

test-watch:
	uv run pytest tests/ -v --looponfail

# =============================================================================
# Aliases
# =============================================================================

up: dev-up
down: dev-down
logs: dev-logs
status: dev-status
build: rebuild

.DEFAULT_GOAL := help
