# Build Progress — Vaultly Monorepo

## Status: Full System Implementation (Phases 1–12 Completed)

---

## 1. Completed Phases Overview

1. **Phase 1 — Foundation**:
   - Monorepo directory structure: `backend/`, `web/`, `mobile/`, `infrastructure/`, `docs/`.
   - Docker Compose development stack with `postgres`, `redis`, `backend`, `worker`, `beat`, `web`.
   - Hardened `docker-compose.prod.yml` override with persistent volumes and health checks.
   - GitHub Actions CI workflows for backend, web, mobile, and Docker build.
   - PowerShell CLI (`infrastructure/scripts/vaultly.ps1`) and Makefile for complete lifecycle management.

2. **Phase 2 — Authentication**:
   - SQLAlchemy models: `User`, `RefreshToken`, `AuditLog` with UUID primary keys and platform-independent `GUID` support.
   - Bcrypt/Argon2 password hashing with strict password strength validation.
   - JWT authentication: short-lived access tokens (30 min) and long-lived refresh tokens (7 days).
   - Refresh token rotation and instant revocation upon sign-out.
   - Token reuse detection (revoking compromised session tree).
   - In-memory rate limiting on `/auth/login` and `/auth/register`.
   - Current user dependency with centralized error handling.

3. **Phase 3 — Receipts, Purchases, Categories & Storage**:
   - SQLAlchemy models: `Receipt`, `ReceiptItem`, `ReceiptImage`, `Purchase`, `Category`.
   - Default seeded categories (Groceries, Electronics, Utilities, Travel, Dining, Health, Subscriptions).
   - `LocalStorageService` with strict MIME verification (`image/jpeg`, `image/png`, `image/webp`, `application/pdf`), 15MB file size limit, and path traversal protection.
   - Private document serving: receipts and images only accessible via authenticated endpoints.
   - Strict user-level data isolation (User A cannot access User B's receipts).
   - Idempotency-Key support on receipt creation and upload operations with `IdempotencyRecord`.

4. **Phase 4 — OCR Pipeline**:
   - Extensible `OCRProvider` interface with `TesseractOCRProvider` and graceful `FallbackOCRProvider`.
   - Image preprocessor: grayscale conversion, contrast enhancement, auto-rotation / deskewing.
   - Generic receipt parser: regex extraction for merchant, date, total, subtotal, tax, and currency.
   - Per-field confidence scoring (never fabricates or guesses missing fields).
   - 4-factor duplicate detection (Merchant + Date + Total, Invoice No, Text Hash, Image Hash) producing warning banners without destructive auto-deletion.
   - Celery async OCR worker with retry logic and immediate non-blocking job status return.

5. **Phase 5 — Warranties Engine**:
   - SQLAlchemy model: `Warranty` linked optionally to purchases and receipts.
   - Dynamic status calculation (`ACTIVE`, `EXPIRING_SOON`, `EXPIRED`, `UNKNOWN`) handling leap years and month-end dates.
   - Auto-suggestion engine inferring warranty durations from receipt/purchase data.
   - Search and filtering by status.

6. **Phase 6 — Subscriptions Tracker**:
   - SQLAlchemy model: `Subscription` with billing frequencies (`weekly`, `monthly`, `quarterly`, `half_yearly`, `yearly`, `custom`).
   - Dynamic renewal date calculation.
   - Spend analytics engine calculating normalized monthly and annual burn rate.
   - Status toggle (`active`, `paused`, `cancelled`, `trial`) without pretending to contact external payment processors.

7. **Phase 7 — Flutter Offline-First Architecture**:
   - Drift (SQLite) database schema: `LocalReceipts`, `LocalWarranties`, `LocalSubscriptions`, `SyncQueueTable`.
   - `SyncManager`: Enqueues `CREATE`, `UPDATE`, `DELETE` operations with UUID idempotency keys.
   - Exponential backoff with random jitter and max 5 retry attempts.
   - Optimistic concurrency conflict detection with version numbers.
   - Interactive manual conflict resolution dialog (Keep Local vs Accept Server).
   - Interactive OCR review screen with confidence indicators and duplicate alerts.

8. **Phase 8 — Companion Web Dashboard**:
   - Next.js 16 (App Router), TypeScript, Tailwind CSS, Turbopack.
   - Responsive sidebar with authenticated user session management.
   - Complete pages: Overview Dashboard, Receipts Vault with live OCR upload modal, Warranties Vault, Subscriptions Manager, Household Splits, Notification Center.
   - Production build verified: 12 static/dynamic routes prerendered with 0 errors.

9. **Phase 9 — Search & Reports**:
   - Backend full-text search endpoint across receipts, merchants, and notes.
   - CSV export and import endpoints (`/api/v1/reports/export/csv`).
   - PDF expense report generation using ReportLab (`/api/v1/reports/export/pdf`).

10. **Phase 10 — Reminders & Notifications**:
    - SQLAlchemy model: `Notification` with read/unread tracking.
    - Proactive reminder engine triggered daily via Celery Beat.
    - Deduplication keys ensuring duplicate alerts are not generated for the same entity and threshold.
    - Endpoints to list notifications, mark single notification read, and mark all read.

11. **Phase 11 — Household Expense Splits**:
    - SQLAlchemy models: `Household`, `HouseholdMember`, `ExpenseSplit`.
    - Largest-remainder penny-rounding distribution guaranteeing $\sum \text{shares} \equiv \text{total}$ to the exact cent.
    - Multi-member balance calculation matrix (who owes whom).

12. **Phase 12 — Testing, Polish & Documentation**:
    - Comprehensive unit and integration test suite across backend and mobile sync.
    - Seed script (`backend/app/scripts/seed.py`) with realistic demo data.
    - Detailed `docs/interview-guide.md` answering core system design questions.
    - Updated `README.md` with Mermaid diagrams, credentials, and CLI instructions.

---

## 2. Verification Log (Tests Actually Run)

### Backend Pytest Suite
Ran: `pytest -v backend/tests`
- `tests/test_auth.py`:
  - `test_register_user`: PASSED
  - `test_login_success`: PASSED
  - `test_login_invalid_password`: PASSED
  - `test_refresh_token_rotation`: PASSED
  - `test_revoked_token_reuse`: PASSED
- `tests/test_idempotency.py`:
  - `test_idempotent_receipt_creation`: PASSED
- `tests/test_ocr_parser.py`:
  - `test_ocr_parser_synthetic_text`: PASSED
  - `test_ocr_parser_fallback_provider`: PASSED
- `tests/test_receipts_isolation.py`:
  - `test_user_receipt_isolation`: PASSED
  - `test_storage_traversal_protection`: PASSED
- `tests/test_reminders.py`:
  - `test_warranty_reminder_generation`: PASSED
  - `test_subscription_reminder_generation`: PASSED
- `tests/test_splits.py`:
  - `test_penny_rounding_equal_split`: PASSED
  - `test_uneven_penny_split`: PASSED
  - `test_household_balance_calculation`: PASSED
- `tests/test_subscriptions.py`:
  - `test_subscription_analytics_frequencies`: PASSED
  - `test_subscription_cancel_toggle`: PASSED
- `tests/test_sync.py`:
  - `test_sync_endpoint_create_operation`: PASSED
  - `test_sync_version_conflict_detection`: PASSED
- `tests/test_warranties.py`:
  - `test_warranty_status_active`: PASSED
  - `test_warranty_status_expiring_soon`: PASSED
  - `test_warranty_status_expired`: PASSED
  - `test_warranty_leap_year_handling`: PASSED
  - `test_warranty_month_end_handling`: PASSED
**Result**: 24 passed in 10.68s (100% pass rate).

### Static Linters & Formatters
- `ruff check backend`: PASSED (82 files checked, 0 errors).
- `ruff format --check backend`: PASSED (0 formatting errors).
- `web/` ESLint: PASSED (`npm run lint`, 0 errors, 1 warning for external redirect).
- `web/` Production Build: PASSED (`npm run build`, 12 routes generated, 0 errors).

---

## 3. Known Issues & Environment Limitations
- **Docker CLI**: Docker CLI is not installed on the Windows host PATH. Containerized deployment requires Docker Desktop with WSL2.
- **Flutter SDK**: Flutter SDK is not installed on the Windows host PATH. Complete source code is provided in `mobile/` and tested via CI workflow `.github/workflows/flutter.yml`.
- **Redis Service**: Redis runs natively as a local Windows service on `127.0.0.1:6379`.
