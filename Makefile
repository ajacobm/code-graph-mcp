.PHONY: help dev-up dev-down dev-logs test-up test-down backend-up backend-down codespaces-up codespaces-down ghcr-up ghcr-down clean rebuild lint test

COMPOSE_BASE := docker-compose -f infrastructure/docker-compose.yml
COMPOSE_TEST := $(COMPOSE_BASE) -f infrastructure/profiles/test.yml
COMPOSE_BACKEND := $(COMPOSE_BASE) -f infrastructure/profiles/backend-only.yml
COMPOSE_CODESPACES := $(COMPOSE_BASE) -f infrastructure/profiles/codespaces.yml
COMPOSE_GHCR := $(COMPOSE_BASE) -f infrastructure/profiles/ghcr.yml
COMPOSE_MULTI := $(COMPOSE_BASE) -f infrastructure/profiles/multi.yml
COMPOSE_VALIDATION := $(COMPOSE_BASE) -f infrastructure/profiles/validation.yml

help:
	@echo "CodeNavigator (codenav) - Make Targets"
	@echo ""
	@echo "Development:"
	@echo "  make dev-up           - Start development stack (Redis, Memgraph, API, Jupyter)"
	@echo "  make dev-down         - Stop development stack"
	@echo "  make dev-logs         - View development logs (follow)"
	@echo "  make dev-status       - Show container status"
	@echo ""
	@echo "Testing:"
	@echo "  make test-up          - Start testing environment"
	@echo "  make test-down        - Stop testing environment"
	@echo "  make test-logs        - View test logs"
	@echo ""
	@echo "Backend Only (Frontend Dev):"
	@echo "  make backend-up       - Start backend services only"
	@echo "  make backend-down     - Stop backend services"
	@echo ""
	@echo "GitHub Codespaces:"
	@echo "  make codespaces-up    - Start Codespaces stack"
	@echo "  make codespaces-down  - Stop Codespaces stack"
	@echo ""
	@echo "GHCR/Registry:"
	@echo "  make ghcr-up          - Start with GHCR configuration"
	@echo "  make ghcr-down        - Stop GHCR stack"
	@echo ""
	@echo "Multi-Service:"
	@echo "  make multi-up         - Start extended services"
	@echo "  make multi-down       - Stop extended services"
	@echo ""
	@echo "CI/Validation:"
	@echo "  make validation-up    - Start validation environment"
	@echo "  make validation-down  - Stop validation environment"
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

# Development Targets
dev-up:
	$(COMPOSE_BASE) up -d
	@echo "✅ Development stack started"

dev-down:
	$(COMPOSE_BASE) down
	@echo "✅ Development stack stopped"

dev-logs:
	$(COMPOSE_BASE) logs -f

dev-status:
	$(COMPOSE_BASE) ps

dev-shell:
	$(COMPOSE_BASE) exec codenav-web bash

# Testing Targets
test-up:
	$(COMPOSE_TEST) up -d
	@echo "✅ Testing environment started"

test-down:
	$(COMPOSE_TEST) down
	@echo "✅ Testing environment stopped"

test-logs:
	$(COMPOSE_TEST) logs -f

test-shell:
	$(COMPOSE_TEST) exec codenav-web bash

# Backend Only (Frontend Dev) Targets
backend-up:
	$(COMPOSE_BACKEND) up -d
	@echo "✅ Backend services started (frontend dev mode)"

backend-down:
	$(COMPOSE_BACKEND) down
	@echo "✅ Backend services stopped"

backend-logs:
	$(COMPOSE_BACKEND) logs -f

backend-shell:
	$(COMPOSE_BACKEND) exec codenav-web bash

# GitHub Codespaces Targets
codespaces-up:
	$(COMPOSE_CODESPACES) up -d
	@echo "✅ Codespaces stack started"

codespaces-down:
	$(COMPOSE_CODESPACES) down
	@echo "✅ Codespaces stack stopped"

codespaces-logs:
	$(COMPOSE_CODESPACES) logs -f

# GHCR Targets
ghcr-up:
	$(COMPOSE_GHCR) up -d
	@echo "✅ GHCR stack started"

ghcr-down:
	$(COMPOSE_GHCR) down
	@echo "✅ GHCR stack stopped"

ghcr-logs:
	$(COMPOSE_GHCR) logs -f

# Multi-Service Targets
multi-up:
	$(COMPOSE_MULTI) up -d
	@echo "✅ Multi-service stack started"

multi-down:
	$(COMPOSE_MULTI) down
	@echo "✅ Multi-service stack stopped"

# CI/Validation Targets
validation-up:
	$(COMPOSE_VALIDATION) up -d
	@echo "✅ Validation environment started"

validation-down:
	$(COMPOSE_VALIDATION) down
	@echo "✅ Validation environment stopped"

validation-logs:
	$(COMPOSE_VALIDATION) logs -f

# Cleanup Targets
clean:
	$(COMPOSE_BASE) down -v
	@echo "✅ All containers and volumes removed"

rebuild:
	$(COMPOSE_BASE) build --no-cache
	@echo "✅ All images rebuilt"

ps:
	$(COMPOSE_BASE) ps

# Code Quality Targets
lint:
	python -m pylint src/codenav --exit-zero
	@echo "✅ Linting complete"

format:
	python -m black src/ tests/
	python -m isort src/ tests/
	@echo "✅ Code formatted"

# Testing Targets
test:
	python -m pytest tests/ -v

test-coverage:
	python -m pytest tests/ --cov=src --cov-report=html
	@echo "✅ Coverage report: htmlcov/index.html"

test-watch:
	python -m pytest tests/ -v --looponfail

# Shorthand aliases
up: dev-up
down: dev-down
logs: dev-logs
status: dev-status
rebuild-all: rebuild

.DEFAULT_GOAL := help
