# Continuous integration (GitHub Actions)

Workflow file: [`.github/workflows/ci.yml`](../.github/workflows/ci.yml)

## Triggers

- Push to `main`
- Pull requests

## Pipeline

```text
push / pull_request
        ↓
GitHub Actions (ubuntu-latest)
        ├─ job: backend
        │     ├─ PostgreSQL 16 (pgvector) service
        │     ├─ pip install -e ".[dev]"
        │     ├─ ruff check .
        │     ├─ alembic upgrade head
        │     └─ pytest
        ├─ job: frontend
        │     ├─ npm install
        │     ├─ npm run lint
        │     ├─ npm run test
        │     └─ npm run build
        └─ job: openapi (needs backend)
              └─ python .github/scripts/check_openapi_paths.py
```

## Secrets

CI does **not** require `GROQ_API_KEY` or AWS credentials. Groq calls in tests are mocked unless opt-in integration markers are enabled locally.

## Local parity

```powershell
cd backend; ruff check .; alembic upgrade head; pytest
cd frontend; npm run lint; npm run test; npm run build
python .github/scripts/check_openapi_paths.py
```

## Agent hook

`agent-hooks/pre-deploy-validation.ps1` mirrors a subset of these checks before any manual container push (local only).
