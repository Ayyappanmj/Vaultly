# Vaultly — Smart Receipt, Warranty & Subscription Vault
Offline-first receipt, warranty and subscription tracker. Status: Phase 1 (foundation).

## Quick start (Windows PowerShell)
    Copy-Item .env.example .env
    docker compose up --build
    curl http://localhost:8000/health
API docs: http://localhost:8000/docs

## Layout
backend/ (FastAPI) · mobile/ (Flutter) · web/ (Next.js) · infrastructure/ · docs/
