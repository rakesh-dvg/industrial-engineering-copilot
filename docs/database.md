# Database

## Engine

- **PostgreSQL 16** with **pgvector** (Docker image `pgvector/pgvector:pg16`)
- Async access: SQLAlchemy 2 + `asyncpg`
- Sync URL for Alembic: `postgresql+psycopg://...`

## Configuration

Set in `.env` (see [.env.example](../.env.example)):

- `DATABASE_URL` — async SQLAlchemy
- `DATABASE_URL_SYNC` — Alembic and sync scripts

Docker Compose overrides hostnames to `postgres:5432`.

## Migrations

All schema changes go through Alembic:

```powershell
cd backend
alembic upgrade head
```

Revision chain (head):

1. `001_initial_foundation` — organizations, users, members
2. `002_product_catalog` — manufacturers, products, specs, pricing
3. `003_product_documents` — documents + pgvector chunks
4. `004_quotations` — quotations and line items
5. `005_comm_followups` — communication + sales follow-ups

Verify locally:

```powershell
alembic heads
alembic current
```

Regression tests: `tests/test_migrations.py` (requires PostgreSQL; fresh DB URL for integration cases).

## Seeds (data, not schema)

After migrations:

```powershell
python -m app.seed.catalog
python -m app.seed.followups
python -m app.seed.documents
```

Seeds are **idempotent** and safe to re-run for demo reset (`.\scripts\reset-demo.ps1`).

## Models

SQLAlchemy models live under `backend/app/models/`. Org scoping fields are present for tenant-ready resources.
