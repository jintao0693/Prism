.PHONY: setup api web infra test lint ci

setup:
	@echo "Use scripts/dev.sh (Unix) or scripts/dev.ps1 (Windows)"

api:
	cd apps/api && .venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

web:
	cd apps/web && npm run dev

infra:
	docker compose -f infra/docker-compose.yml up -d

test:
	cd apps/api && .venv/bin/pytest -q

lint:
	cd apps/api && .venv/bin/ruff check app
	cd apps/web && npm run lint

ci: lint test
	cd apps/web && npm run build
