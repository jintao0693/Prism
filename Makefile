# Unix-oriented helpers. On Windows prefer: .\scripts\dev.ps1
.PHONY: setup api web infra test lint ci help

PYTHON ?= python3
VENV_BIN := apps/api/.venv/bin

help:
	@echo "Targets: setup api web infra test lint ci"
	@echo "Windows: use scripts/dev.ps1 instead of make api/test"

setup:
	@echo "Use scripts/dev.sh (Unix) or scripts/dev.ps1 (Windows)"

api:
	cd apps/api && $(VENV_BIN)/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

web:
	cd apps/web && npm run dev

infra:
	docker compose -f infra/docker-compose.yml up -d

test:
	cd apps/api && $(VENV_BIN)/python -m pytest -q

lint:
	cd apps/api && $(VENV_BIN)/python -m ruff check app
	cd apps/web && npm run lint

ci: lint test
	cd apps/web && npm run build
