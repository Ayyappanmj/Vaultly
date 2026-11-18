# Vaultly engineering rules (always apply)

Project: Vaultly — Smart Receipt, Warranty & Subscription Vault.
Monorepo: backend/ (FastAPI), mobile/ (Flutter), web/ (Next.js), infrastructure/, docs/.
Host OS: Windows with PowerShell. Give PowerShell commands, not bash-only ones. Use Docker for Postgres/Redis.

Truthfulness
- Never claim a feature works, or tests pass, unless you ran it and saw the output.
- Never fabricate OCR results, analytics, exchange rates or business data.
- If a tool (Flutter SDK, Node, Docker) is missing or a command fails, say so and stop that task; do not fake it.

Technology (free/open-source only, no paid APIs, no AWS/Cloudflare/Firebase required)
- Backend: Python 3.11, FastAPI, Pydantic v2, SQLAlchemy 2.x, PostgreSQL, Alembic, Redis, Celery, Argon2 or bcrypt, JWT.
- OCR: Tesseract behind an OCRProvider interface (PaddleOCR optional adapter). Must work with no API keys.
- Mobile: Flutter, Riverpod, Drift/SQLite, GoRouter, Dio, camera, local notifications.
- Web: Next.js App Router, TypeScript, Tailwind, shadcn/ui, React Query, Zod, Recharts.
- Tests: Pytest, Flutter Test, Playwright. CI: GitHub Actions. Storage: local filesystem behind a storage abstraction (MinIO optional).

Code quality
- Clean, readable, beginner-explainable code; meaningful names; minimal dependencies; no unnecessary abstractions.
- Validate all input; handle errors; implement loading, empty and error states and retries in UI.
- Config via environment variables; never commit secrets; keep .env.example current.
- No placeholder buttons, no TODO for core functionality.
- Private documents are served only through authenticated endpoints; do not log receipt contents.

Workflow
- Before editing, read docs/build-progress.md and inspect the existing files. Preserve working files; do not regenerate completed modules.
- Work in small steps. Fix existing failures before adding new modules.
- After each task: run the relevant tests/linters, fix failures, then update docs/build-progress.md
  (completed phases, files created/modified, tests executed/passed/failed, known issues, exact next task).
- Keep chat summaries short. Do not paste whole source files into chat.
