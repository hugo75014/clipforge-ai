.PHONY: help install build up down restart logs ps clean test lint format audit

# -------- helpers --------
help:
	@echo "ClipForge AI — make targets"
	@echo "  install    Install frontend + backend dependencies locally"
	@echo "  up         docker compose up -d --build"
	@echo "  down       docker compose down"
	@echo "  restart    docker compose restart"
	@echo "  logs       docker compose logs -f"
	@echo "  ps         docker compose ps"
	@echo "  test       Run all tests"
	@echo "  lint       Run linters"
	@echo "  format     Format code"
	@echo "  audit      Run pre-flight audit (tsc, python, envs, …)"
	@echo "  clean      Remove generated artifacts"

# -------- install --------
install:
	@echo "Installing frontend deps..."
	cd frontend && npm install
	@echo "Installing backend deps..."
	cd backend && python -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"

# -------- docker --------
up:
	docker compose up -d --build

down:
	docker compose down

restart:
	docker compose restart

logs:
	docker compose logs -f

ps:
	docker compose ps

# -------- tests --------
test:
	cd backend && pytest -q
	cd frontend && npm test --silent

test-e2e:
	cd backend && pytest -q tests/e2e

# -------- quality --------
lint:
	cd backend && ruff check . && mypy app
	cd frontend && npm run lint

format:
	cd backend && ruff format .
	cd frontend && npm run format

# -------- audit --------
audit:
	@bash scripts/audit.sh

# -------- clean --------
clean:
	rm -rf frontend/dist frontend/node_modules
	rm -rf backend/.venv backend/build backend/dist
	rm -rf data/uploads/* data/temp/* data/outputs/* data/logs/*
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
