.PHONY: setup dev test lint migrate seed clean help

help:
	@echo "Available commands:"
	@echo "  setup   - Initialize environment files and directories"
	@echo "  dev     - Start full stack in Docker Compose"
	@echo "  test    - Run backend and web tests"
	@echo "  lint    - Run backend and web linters"
	@echo "  migrate - Run database migrations with Alembic"
	@echo "  seed    - Seed initial database data"
	@echo "  clean   - Stop containers and delete volumes and caches"

setup:
	@test -f .env || cp .env.example .env
	@mkdir -p uploads

dev:
	docker compose up --build

test:
	cd backend && pytest
	@if [ -d "web/node_modules" ]; then cd web && npm run lint; fi

lint:
	cd backend && ruff check . && ruff format --check .
	@if [ -d "web/node_modules" ]; then cd web && npm run lint; fi

migrate:
	docker compose exec backend alembic upgrade head || (cd backend && alembic upgrade head)

seed:
	docker compose exec backend python -m app.scripts.seed || (cd backend && python -m app.scripts.seed)

clean:
	docker compose down -v --remove-orphans
	rm -rf uploads/* backend/.pytest_cache backend/.ruff_cache web/.next
