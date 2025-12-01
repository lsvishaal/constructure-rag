# =============================================================================
# CONSTRUCTURE RAG - Development Makefile
# =============================================================================
# Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
# =============================================================================

.PHONY: run run-backend run-frontend build build-clean down logs test ingest status restart pull-model help clean rebuild-streamlit

GREEN  := \033[0;32m
YELLOW := \033[0;33m
CYAN   := \033[0;36m
RED    := \033[0;31m
NC     := \033[0m

BACKEND_DIR  := backend
FRONTEND_DIR := frontend

.DEFAULT_GOAL := help

# =============================================================================
# MAIN COMMANDS - Start Everything
# =============================================================================

# Start backend (detached) then frontend (foreground) - RECOMMENDED
dev: run-backend
	@echo "$(GREEN)✓ Backend running. Starting frontend...$(NC)"
	@echo "$(CYAN)  Press Ctrl+C to stop frontend$(NC)"
	cd $(FRONTEND_DIR) && npm run dev

# Start everything detached (backend + frontend in background)
run: run-backend run-frontend
	@echo "$(GREEN)✓ Constructure RAG is running!$(NC)"
	@echo "  Backend API:   http://localhost:8000"
	@echo "  Frontend:      http://localhost:3000"
	@echo "  Streamlit UI:  http://localhost:8501"
	@echo ""
	@echo "$(YELLOW)Tip: Use 'make dev' for frontend with live output$(NC)"

run-backend:
	@echo "$(CYAN)→ Starting backend services...$(NC)"
	cd $(BACKEND_DIR) && docker compose up -d
	@echo "$(GREEN)✓ Backend services started$(NC)"

run-frontend:
	@echo "$(CYAN)→ Starting frontend dev server (background)...$(NC)"
	@cd $(FRONTEND_DIR) && nohup npm run dev > /tmp/frontend.log 2>&1 &
	@sleep 3
	@echo "$(GREEN)✓ Frontend started on http://localhost:3000$(NC)"
	@echo "$(CYAN)  Logs: tail -f /tmp/frontend.log$(NC)"

build:
	@echo "$(CYAN)→ Building backend containers...$(NC)"
	cd $(BACKEND_DIR) && docker compose build
	@echo "$(GREEN)✓ Build complete$(NC)"

build-clean:
	@echo "$(YELLOW)→ Building backend (no cache)...$(NC)"
	cd $(BACKEND_DIR) && docker compose build --no-cache
	@echo "$(GREEN)✓ Clean build complete$(NC)"

rebuild: down build-clean run
	@echo "$(GREEN)✓ Full rebuild complete$(NC)"

rebuild-streamlit:
	@echo "$(CYAN)→ Rebuilding Streamlit container...$(NC)"
	cd $(BACKEND_DIR) && docker compose stop streamlit && docker compose build --no-cache streamlit && docker compose up -d streamlit
	@echo "$(GREEN)✓ Streamlit rebuilt$(NC)"

down:
	@echo "$(CYAN)→ Stopping backend services...$(NC)"
	cd $(BACKEND_DIR) && docker compose down
	@echo "$(GREEN)✓ Backend stopped$(NC)"
	@echo "$(CYAN)→ Stopping frontend...$(NC)"
	-@pkill -f "next dev" 2>/dev/null || true
	@echo "$(GREEN)✓ All services stopped$(NC)"

stop: down

restart:
	@echo "$(CYAN)→ Restarting backend...$(NC)"
	cd $(BACKEND_DIR) && docker compose restart
	@echo "$(GREEN)✓ Restarted$(NC)"

restart-streamlit:
	@echo "$(CYAN)→ Restarting Streamlit...$(NC)"
	cd $(BACKEND_DIR) && docker compose restart streamlit
	@echo "$(GREEN)✓ Streamlit restarted$(NC)"

status:
	@echo "$(CYAN)Docker containers:$(NC)"
	@docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "constructure|NAMES" || echo "No containers"
	@echo ""
	@echo "$(CYAN)Frontend:$(NC)"
	@pgrep -f "next dev" > /dev/null && echo "$(GREEN)Running$(NC)" || echo "$(RED)Not running$(NC)"

logs:
	cd $(BACKEND_DIR) && docker compose logs -f backend

logs-all:
	cd $(BACKEND_DIR) && docker compose logs -f

test:
	@echo "$(CYAN)→ Running tests...$(NC)"
	cd $(BACKEND_DIR) && uv run pytest tests/ -v
	@echo "$(GREEN)✓ Tests complete$(NC)"

test-fast:
	@echo "$(CYAN)→ Running fast tests...$(NC)"
	cd $(BACKEND_DIR) && uv run pytest tests/ -v -m "not slow"
	@echo "$(GREEN)✓ Done$(NC)"

lint:
	@echo "$(CYAN)→ Running linter...$(NC)"
	cd $(BACKEND_DIR) && uv run ruff check src/
	@echo "$(GREEN)✓ Lint complete$(NC)"

ingest:
	@echo "$(CYAN)→ Re-ingesting documents...$(NC)"
	cd $(BACKEND_DIR) && docker compose exec backend python -m src.cli ingest --dir /app/Assets
	@echo "$(GREEN)✓ Ingestion complete$(NC)"

pull-model:
	@echo "$(CYAN)→ Pulling llama3.2 model...$(NC)"
	docker exec constructure-ollama ollama pull llama3.2
	@echo "$(GREEN)✓ Model pulled$(NC)"

shell:
	docker exec -it constructure-backend bash

shell-ollama:
	docker exec -it constructure-ollama bash

clean:
	@echo "$(YELLOW)→ Cleaning containers...$(NC)"
	cd $(BACKEND_DIR) && docker compose down -v
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

clean-all:
	@echo "$(RED)→ Removing all containers and images...$(NC)"
	cd $(BACKEND_DIR) && docker compose down -v --rmi local
	@echo "$(GREEN)✓ Full cleanup complete$(NC)"

help:
	@echo "$(CYAN)╔═══════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(CYAN)║       CONSTRUCTURE RAG - Development Commands             ║$(NC)"
	@echo "$(CYAN)╚═══════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(GREEN)QUICK START:$(NC)"
	@echo "  make dev          Start all + frontend in foreground (RECOMMENDED)"
	@echo "  make run          Start all in background"
	@echo "  make down         Stop all services"
	@echo ""
	@echo "$(GREEN)BUILD:$(NC)"
	@echo "  make build        Build backend containers"
	@echo "  make build-clean  Build with no cache (fresh rebuild)"
	@echo "  make rebuild      Stop, clean build, and restart"
	@echo ""
	@echo "$(GREEN)SERVICES:$(NC)"
	@echo "  make status       Show status of all services"
	@echo "  make restart      Restart backend services"
	@echo "  make logs         Follow backend logs"
	@echo "  make logs-all     Follow all container logs"
	@echo ""
	@echo "$(GREEN)DEVELOPMENT:$(NC)"
	@echo "  make test         Run backend tests"
	@echo "  make lint         Run linter"
	@echo "  make ingest       Re-ingest PDF documents"
	@echo "  make pull-model   Pull LLM model in Ollama"
	@echo "  make shell        Open shell in backend container"
	@echo ""
	@echo "$(GREEN)CLEANUP:$(NC)"
	@echo "  make clean        Remove containers and volumes"
	@echo "  make clean-all    Remove everything (full reset)"
	@echo ""
	@echo "$(CYAN)Endpoints:$(NC)"
	@echo "  Backend API:   http://localhost:8000"
	@echo "  API Docs:      http://localhost:8000/docs"
	@echo "  Frontend:      http://localhost:3000"
	@echo "  Streamlit:     http://localhost:8501"
