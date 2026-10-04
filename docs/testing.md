# Testing strategy

## Automated (CI and local)

| Layer | Command | What it covers |
|-------|---------|----------------|
| Backend unit/integration | `cd backend && pytest` | Validation, recommendations, quotations, communication, seeds, migrations (opt-in DB) |
| Backend lint | `cd backend && ruff check .` | Python style and common bugs |
| Frontend unit | `cd frontend && npm run test` | Sales Dashboard workflow, follow-ups (27 tests) |
| Frontend lint/build | `npm run lint && npm run build` | TypeScript and production bundle |
| OpenAPI contract | `python .github/scripts/check_openapi_paths.py` | Every path in `openapi.yaml` exists on FastAPI app |
| MCP demo server | `cd mcp-server && pip install -e . && pytest` | In-memory catalog tools |

GitHub Actions runs backend (with PostgreSQL service), frontend, and OpenAPI jobs — see [cicd.md](cicd.md).

### Local backend prerequisites

Most backend tests need PostgreSQL:

```powershell
docker compose up -d postgres
cd backend
$env:TEST_DATABASE_URL = "postgresql+asyncpg://iec:iec@localhost:5432/iec"
pytest
```

Migration integration tests (`tests/test_migrations.py`, marked `@pytest.mark.integration`) use a separate database (`iec_migration_fresh` by default) and **sync psycopg** — run on Linux CI or ensure `psycopg[binary]` is installed on Windows.

### Optional live Groq tests

Set `RUN_GROQ_INTEGRATION_TESTS=true` and `GROQ_API_KEY` locally. CI does **not** require Groq secrets.

## Local integration testing (Docker Compose)

```text
Browser → Frontend (Vite dev or Nginx prod compose)
              ↓
         FastAPI backend (:8020)
              ↓
    PostgreSQL + Redis + MinIO
```

**Development stack:** `docker compose up` (see root `docker-compose.yml`).

**Production-like stack:** `docker compose -f docker-compose.prod.yml up --build` → UI on http://localhost:8080.

Manual CEO workflow: [CEO-demo-script.md](CEO-demo-script.md).

## Historical AWS end-to-end validation

The application was deployed to **AWS ECS Fargate + ALB + RDS PostgreSQL + S3 + Secrets Manager** and validated remotely through:

```text
RFQ extraction → validation → evidence → recommendation
→ sales decision → quotation → approval → communication → send → follow-up
```

That environment was **intentionally destroyed** after the demo video was recorded. Reviewers should not expect a live AWS URL; reproduce the workflow locally with Docker Compose.

Evidence: [architecture.md](architecture.md), [aws-mvp-deployment.md](aws-mvp-deployment.md), `tests/test_integration_workflow.py`.

## Agent hooks (pre-flight)

```powershell
.\agent-hooks\pre-deploy-validation.ps1
.\agent-hooks\pre-commit-security-check.ps1
```

These run local checks only — no AWS deployment.
