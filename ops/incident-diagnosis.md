# Incident diagnosis (local MVP)

## Backend will not start

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| DB connection error | PostgreSQL not running | `docker compose up -d postgres` |
| Relation does not exist | Migrations not applied | `cd backend && alembic upgrade head` |
| Groq not configured | Missing `GROQ_API_KEY` | Set in `.env` (backend only) for live extract |
| Import error multipart | Old image | Rebuild backend; `python-multipart` in `pyproject.toml` |

## Frontend cannot reach API

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| CORS error | Origin not in `CORS_ORIGINS` | Match Vite URL in `.env` |
| 404 on `/api` in prod compose | Nginx proxy | Set `BACKEND_API_URL` in frontend container |
| Wrong API host | Stale `VITE_API_BASE_URL` | Use `http://localhost:8020` for local dev |

## Seeds fail

Run **`alembic upgrade head`** before `python -m app.seed.catalog`. Seeds do not create tables.

## Historical AWS (reference only)

ECS task exits, unhealthy target group, RDS security group — see [docs/aws-mvp-deployment.md](../docs/aws-mvp-deployment.md). Infrastructure is **no longer running**.

## Audit logging

| Action | Status |
|--------|--------|
| Quotation status changes | **Implemented** (DB records) |
| Communication send (demo) | **Implemented** (`sent_at`, demo flag) |
| Follow-up updates | **Implemented** |
| Central SIEM export | **Planned** (not in MVP) |
| CloudTrail for past AWS demo | **Demonstrated** during deployment learning |
