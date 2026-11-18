# Build Progress

## Current phase: 1 — Foundation (Completed)

## Completed Phases
- **Phase 1 — Foundation**: Completed and verified.

## Files Created / Modified
- `.agent/rules/vaultly.md` — Workspace engineering rules.
- `.agent/workflows/continue-phase.md` — Reusable phase continuation workflow.
- `docs/phases.md` — Complete 12-phase specification and acceptance criteria.
- `docs/build-progress.md` — Updated phase tracking and verification logs.
- `backend/app/main.py` — Added connection timeouts (2s) to `/health` database and Redis probes to prevent hung health checks when services are degraded.
- `backend/.dockerignore` — Added ignores for python cache, pytest, ruff, venv.
- `web/` — Initialized Next.js (App Router, TypeScript, Tailwind CSS, ESLint).
- `web/app/layout.tsx` & `web/app/globals.css` — Configured system font stack for offline-first resilience.
- `web/app/api/health/route.ts` — Added web health check endpoint.
- `web/Dockerfile` & `web/.dockerignore` — Multi-stage production container build.
- `web/{components,features,hooks,lib,types}` — Folder layout established.
- `mobile/lib/{core,common,features,data,domain,services}` — Folder layout established.
- `docker-compose.yml` — Added `beat` (Celery Beat) and `web` services with health checks and persistent volumes (`pgdata`, `redisdata`, `uploads`).
- `docker-compose.prod.yml` — Created production compose override.
- `.github/workflows/backend.yml` — CI workflow for backend (ruff, pytest, alembic check).
- `.github/workflows/web.yml` — CI workflow for web (eslint, tsc, build).
- `.github/workflows/flutter.yml` — CI workflow for mobile (analyze, test).
- `.github/workflows/docker.yml` — CI workflow for container images build.
- `Makefile` — Extended with `setup`, `dev`, `test`, `lint`, `migrate`, `seed`, `clean`.
- `infrastructure/scripts/vaultly.ps1` — PowerShell management CLI supporting all targets.
- `infrastructure/scripts/setup.ps1` — Delegated to `vaultly.ps1 setup`.
- `.gitignore` — Added `uploads/`, `redisdata/`, `.pytest_cache/`, `.ruff_cache/`.

## Tests Executed & Passed
- `pytest backend/tests/test_health.py`: 1 passed.
- `ruff check backend`: passed (0 issues).
- `ruff format --check backend`: passed (15 files formatted).
- `npm run lint` (web): passed (0 issues).
- `npm run build` (web): passed (compiled, typecheck passed, static route `/api/health` and pages generated).
- `powershell -ExecutionPolicy Bypass -File .\infrastructure\scripts\vaultly.ps1 lint`: passed.
- `powershell -ExecutionPolicy Bypass -File .\infrastructure\scripts\vaultly.ps1 test`: passed (runs backend pytest and web build check).

## Known Issues / Tool Status
- **Docker**: `docker` CLI is not installed or not in PATH on this Windows host.
  - *Action required for full local Docker stack*: Install Docker Desktop for Windows with WSL2 backend.
- **Flutter SDK**: `flutter` is not installed or not in PATH.
  - *Action required before Phase 7*: Download Flutter SDK (version 3.x), add to PATH, and run `flutter create --org com.vaultly --project-name vaultly .` inside `mobile/`.
- **Local Services**: Redis is running locally as a Windows service on `127.0.0.1:6379`. PostgreSQL is not running as a local Windows service.

## Exact Next Task
- Await user approval to proceed to **Phase 2 — Authentication** (SQLAlchemy models + Alembic migrations for users, refresh_tokens, audit_logs; Argon2 password hashing; register/login/logout/refresh rotation endpoints; client auth interfaces).
