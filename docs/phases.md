# Vaultly Implementation Phases

## Overview
Vaultly is a smart receipt, warranty, and subscription vault: a personal vault for receipts, purchases, warranties, and subscriptions with OCR, reminders, search, analytics, offline-first mobile sync, and household expense splitting. Mobile (Flutter) is the primary product; the Next.js web dashboard is the companion for analytics, bulk import, and reports. It runs entirely on free/open-source tooling.

---

## Phase 1 — Foundation
- **Monorepo structure**: `backend/` (FastAPI), `mobile/` (Flutter), `web/` (Next.js), `infrastructure/`, `docs/`.
- **Backend**: FastAPI app with `/health` reporting real PostgreSQL and Redis connectivity, Celery app configured with Redis broker and result backend.
- **Docker Compose**: `postgres`, `redis`, `backend`, `worker`, `celery-beat`, and `web` services with health checks and persistent volumes. `docker-compose.prod.yml` override.
- **Tooling & Scripts**: Makefile and PowerShell scripts (`setup.ps1`) covering setup, dev, test, lint, migrate, seed, clean.
- **CI/CD**: GitHub Actions workflows for backend (ruff, pytest, alembic check), web (eslint, tsc, build), flutter (analyze, test), and docker build.
- **Verification**: Backend tests (`pytest`) and linter (`ruff`).

## Phase 2 — Authentication
- **Models & Migrations**: SQLAlchemy 2.x models + Alembic migrations for `users`, `refresh_tokens`, `audit_logs` (UUID PKs, timestamps, constraints, indexes).
- **Core Auth**: Registration, login, logout, refresh token rotation and revocation; Argon2 password hashing; strict password validation; protected-route dependency; rate limiting on auth endpoints; centralized exception handling; structured logging.
- **Client Auth Integration**:
  - Mobile: secure token storage design (`flutter_secure_storage`), login and registration screens.
  - Web: login page, session handling, protected routes.
- **Verification**: Pytest covering registration, login, token refresh rotation, reuse detection of revoked tokens, authorization; migration applies cleanly on fresh DB.

## Phase 3 — Receipts, Purchases, Categories & File Storage
- **Models & Migrations**: `receipts`, `receipt_images`, `receipt_items`, `purchases`, `categories`, `documents`. Default system categories + custom user categories. Soft deletes.
- **Core Operations**: CRUD with pagination, filtering, sorting; strict user-level data isolation.
- **Storage Abstraction**: Local filesystem storage behind a clean storage provider abstraction (optional MinIO adapter); file upload validation (MIME type, file size); authenticated file download endpoints only.
- **Idempotency**: `Idempotency-Key` header support for receipt creation and uploads (persisted idempotency key, user ID, endpoint, request hash, response; conflicting payload rejected).
- **Verification**: Unit/integration tests for user data isolation (user A cannot read user B's receipt), file upload validation, and idempotent create.

## Phase 4 — OCR (Optical Character Recognition)
- **Architecture**: `OCRProvider` interface; Tesseract OCR implementation; optional graceful fallback / adapter for PaddleOCR (zero paid APIs or keys).
- **Processing Pipeline**: Image preprocessing (grayscale, contrast, deskew/rotate, resize); text normalization; generic receipt parser (merchant, date, receipt number, subtotal, tax, total, currency, payment method, line items) with per-field confidence scoring; uncertain fields flagged, never invented. Merchant-specific parsing strategies behind an extensible registry.
- **Async Processing**: `ocr_jobs` table; Celery task with exponential backoff retry; API returns job status immediately (non-blocking); receipts remain unconfirmed until user review.
- **Duplicate Detection**: Multi-factor duplicate detection (merchant + date + total, receipt number, OCR text hash, perceptual image hash) producing a warning (never auto-deleting).
- **Review UI**: Mobile OCR review screen and web review view: editable fields, visual confidence indicators, Confirm / Edit / Retry / Cancel actions.
- **Verification**: Parser unit tests using synthetic receipt text fixtures (clearly fictional); real Tesseract execution on generated sample image; graceful fallback test when OCR provider is unavailable.

## Phase 5 — Warranties
- **Models & CRUD**: Warranty tracking linked to purchases/receipts, duration tracking, document attachments.
- **Status Engine**: Status calculation (`ACTIVE`, `EXPIRING_SOON`, `EXPIRED`, `UNKNOWN`); custom warranty durations; automatic warranty suggestions from purchase metadata.
- **UI & Alerts**: Reminder preferences, dashboard sections, search/filter by status and expiration.
- **Verification**: Date calculation tests including month-end, leap-year, and timezone edge cases.

## Phase 6 — Subscriptions
- **Models & CRUD**: Subscription tracking, trial tracking, service metadata.
- **Billing Frequencies**: Weekly, monthly, quarterly, half-yearly, yearly, custom.
- **Status Engine**: `active`, `paused`, `cancelled`, `trial`. Next-renewal date calculation; normalized monthly and annual cost equivalents (e.g., weekly = amount × 52 / 12).
- **Analytics & Lifecycle**: Subscription analytics endpoints; cancelling marks status locally (never pretends to cancel externally).
- **Verification**: Calculation tests for every frequency; exclusion of paused/cancelled subscriptions from active spending totals.

## Phase 7 — Flutter Offline-First Architecture & Sync
- **Local Storage**: Drift / SQLite schema mirroring server entities; repository pattern reading local cache first; local image file storage; offline search over SQLite (FTS5 where supported).
- **Sync Engine**: Sync queue tracking `CREATE` / `UPDATE` / `DELETE` operations (operation ID, entity ID/type, user ID, timestamp, retry count, status `PENDING`/`SYNCING`/`SYNCED`/`FAILED`/`CONFLICT`, payload).
- **Resilience**: Connectivity detection; idempotency keys; exponential backoff with jitter; max retries; sync history; version-number conflict detection with manual resolution for receipts/purchases; Sync Status screen.
- **Backend Sync API**: `/api/v1/sync` endpoint that is idempotent (duplicate sync operations never duplicate receipts).
- **Verification**: Flutter tests for queue processing, retry/backoff, conflict resolution; backend test for duplicate sync idempotency.

## Phase 8 — Web Companion Dashboard
- **Views & Pages**: Login, dashboard overview, receipt vault + detail view, bulk import (multi-image/PDF with validation, queue status, history, failed-import retry), purchases, warranties, subscriptions + analytics, spending analytics, budgets, notifications, settings.
- **Design & Standards**: Light theme default with optional dark mode; responsive sidebar layout; shadcn/ui + Tailwind styling; real API integration with zero hardcoded numbers.
- **Verification**: TypeScript checks (`tsc`), linter (`eslint`), build (`next build`), and Playwright smoke tests for login and dashboard.

## Phase 9 — Full-Text Search & Reports
- **Search Engine**: PostgreSQL full-text search using `tsvector` columns/triggers (or generated columns) and GIN indexes; ranked `tsquery` search across merchant, line items, receipt number, category, OCR text, notes, warranties, subscriptions; multi-facet filtering (date range, category, merchant, amount, document type). Example: searching "USB-C cable" matches a receipt via its line item.
- **Reporting & Export**: CSV import/export; PDF expense report generation (Celery background job for large exports).
- **Verification**: Search ranking tests; CSV round-trip tests; PDF generation and integrity verification.

## Phase 10 — Reminders & Notifications
- **Scheduling**: Celery Beat schedules; default reminder rules (return window: 3d; warranty expiration: 30d, 7d, 1d; subscription renewal: 7d, 3d, 1d; trial expiration: 48h); configurable notification timing.
- **Deduplication & Reliability**: Unique deduplication key per `(entity, rule, due_date)`; retry mechanism; reminder status and notification audit history; budget threshold alerts.
- **Delivery**: In-app notifications API (read/unread/mark all/delete); web notification centre; mobile local notifications (operating fully without Firebase).
- **Verification**: Tests verifying reminders are never duplicated and timing configurations are respected.

## Phase 11 — Household & Expense Splitting
- **Models & Splits**: `households`, `household_members`, `expense_splits`; shared receipts and folders.
- **Split Modes**: Equal, percentage, and custom amount splits (with deterministic rounding algorithms ensuring sum of parts equals total amount).
- **Balances & Ingestion**: Balance calculation engine without external payment processing; multi-currency support with manual rates and clearly labeled demo rates only.
- **Email Ingestion**: `POST /api/v1/email-ingestion` endpoint with modular provider adapter interface.
- **Verification**: Split and balance calculation tests including rounding edge cases.

## Phase 12 — Testing, Hardening & Finalization
- **Seed Data**: Comprehensive, clearly fictional seed data; demo credentials documented in README.
- **Testing**: End-to-end verification across backend, Flutter, and web; full test suite execution with documented counts.
- **Security & Quality**: User isolation audit, file access controls, rate limiting verification, secret leak scan, database index optimization, N+1 query review.
- **Documentation**: Final README with Mermaid architecture and sequence diagrams, screenshot checklist, and `docs/interview-guide.md`.
