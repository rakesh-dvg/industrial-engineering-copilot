# AI-assisted development workflow

This project was built incrementally (Phases 1–10) using **Cursor AI coding assistants** alongside human review, OpenAPI-first design, and automated tests. The assistant did not replace engineering judgment: deterministic validation, recommendation gates, and quotation rules remain in Python services with regression tests.

## How AI was used

| Practice | Application in this repo |
|----------|----------------------------|
| Small scoped prompts | Phase-by-phase delivery in `AGENTS.md` (catalog → RFQ → validation → …) |
| Specifications as guardrails | `product-spec.md`, `docs/target-architecture.md`, `openapi.yaml` |
| Review before merge | Human review of diffs; `ruff`, `pytest`, Vitest, CI on GitHub Actions |
| Tests as acceptance | Architecture invariant tests, integration workflow test, frontend Sales Dashboard tests |
| Debugging with logs | AWS ECS CloudWatch and local FastAPI traces during deployment hardening |

## Real examples

Each row follows: **Problem → AI-assisted approach → Human review → Validation → Result**.

### 1. Missing `python-multipart` on AWS

| | |
|---|---|
| **Problem** | Backend task failed at runtime when handling multipart uploads; dependency was not installed in the container image. |
| **AI-assisted approach** | Assistant traced FastAPI upload routes and container build logs, then added `python-multipart` to `backend/pyproject.toml`. |
| **Human review** | Confirmed only document upload paths need multipart; no unrelated deps added. |
| **Validation** | Rebuilt backend image; smoke-tested upload endpoint locally. |
| **Result** | Dependency pinned in `pyproject.toml`; ECS task starts cleanly. |

### 2. Groq base URL normalization

| | |
|---|---|
| **Problem** | Setting `GROQ_BASE_URL=https://api.groq.com/openai/v1` doubled path segments because the Groq SDK already appends `/openai/v1`. |
| **AI-assisted approach** | Implemented `normalize_groq_base_url()` in `app/llm/config.py` and documented host-only URL in `.env.example`. |
| **Human review** | Verified against Groq SDK behavior and kept default `https://api.groq.com`. |
| **Validation** | `tests/test_llm_groq.py` covers suffix stripping and client configuration. |
| **Result** | Misconfiguration surfaces in validation status instead of opaque 404 errors. |

### 3. Frontend Nginx production configuration

| | |
|---|---|
| **Problem** | Production SPA needed same-origin `/api/*` proxy to the backend on AWS (single ALB URL). |
| **AI-assisted approach** | Switched to **`frontend/nginx.conf.template`** with `BACKEND_API_URL` env substitution at container start; empty `VITE_API_BASE_URL` for browser-relative API calls. |
| **Human review** | Checked ALB path rules and ECS task env for frontend service. |
| **Validation** | `docker-compose.prod.yml` local stack on port 8080; CEO demo on AWS. |
| **Result** | One public URL for demo; template documented in README and Dockerfiles. |

### 4. Database migration and seed ordering

| | |
|---|---|
| **Problem** | Seeds failed with missing-table errors when run before Alembic. |
| **AI-assisted approach** | Documented “migrations before seeds” in `AGENTS.md` and added `app/seed/db_checks.py` plus migration regression tests. |
| **Human review** | Ensured seeds remain idempotent and never create schema. |
| **Validation** | `tests/test_migrations.py`, CI `alembic upgrade head` step. |
| **Result** | Repeatable local and AWS bootstrap: `alembic upgrade head` then `python -m app.seed.catalog`. |

### 5. End-to-end testing

| | |
|---|---|
| **Problem** | Need proof that RFQ → quotation → send → follow-up respects architecture boundaries. |
| **AI-assisted approach** | Added `tests/test_integration_workflow.py` and `tests/test_architecture_invariants.py`; expanded Vitest coverage for Sales Dashboard. |
| **Human review** | Confirmed mocks for Groq in tests; no live API key in CI. |
| **Validation** | GitHub Actions backend + frontend jobs; local `pytest` with PostgreSQL. |
| **Result** | Automated CEO demo chain guarded in CI. |

### 6. AWS deployment troubleshooting

| | |
|---|---|
| **Problem** | ECS tasks unhealthy, RDS connectivity, Secrets Manager env injection, CORS for ALB hostname. |
| **AI-assisted approach** | Iterated on task definitions in `deploy/aws/`, security groups, and env vars using CloudWatch log snippets. |
| **Human review** | Cost and scope kept to MVP (no EKS/Terraform). |
| **Validation** | Successful end-to-end demo on public ALB URL (~45s mobile recording). |
| **Result** | Documented in [aws-mvp-deployment.md](aws-mvp-deployment.md); **infrastructure later decommissioned** after learning objective met. |

### 7. Security and repository cleanup

| | |
|---|---|
| **Problem** | Ensure API keys stay out of git and frontend bundles. |
| **AI-assisted approach** | `.env.example` placeholders, `.gitignore` for `.env`, agent hook `agent-hooks/pre-commit-security-check.ps1`, `security/` docs. |
| **Human review** | Rotated any keys that appeared in local-only files; verified `GROQ_API_KEY` not in `VITE_*`. |
| **Validation** | Pre-commit hook + Bandit scan (`security/bandit-report.txt`). |
| **Result** | Groq credentials backend-only; demo email remains simulated. |

## Prompt pattern that worked

```text
Context: AGENTS.md phase scope + openapi.yaml endpoint
Task: Implement <single feature> with tests
Constraints: deterministic validation authority, org scoping, minimal diff
Done when: pytest / vitest / ruff pass
```

## What AI did not do

- Autonomous product or pricing decisions
- Production AWS provisioning after demo teardown
- Inventing manufacturer specifications
