# Agent Instructions — Industrial Engineering Copilot

## Project identity

- **Name:** Industrial Engineering Copilot
- **Tagline:** From Engineering Requirements to Product Decisions
- **Architecture source of truth:** `docs/target-architecture.md`
- **API contract:** `openapi.yaml`

## Engineering principles

1. **OpenAPI-first** — Update `openapi.yaml` when adding API endpoints.
2. **Deterministic validation** — PASS/FAIL/UNKNOWN for spec checks; never invent specs.
3. **Org scoping** — Every tenant resource must include `organization_id` enforcement.
4. **Evidence traceability** — Recommendations must link to structured specs or document citations.
5. **Minimal diffs** — Match existing conventions; avoid unrelated changes.
6. **Groq-only LLM** — Use the backend Groq client in `app/llm/`. Never add alternate LLM providers or expose `GROQ_API_KEY` to the frontend.
7. **LLM is not the decision engine** — Groq may extract, explain, or draft; deterministic validation must never be overridden by model output.
8. **Recommendation is not autonomous sales** — The recommendation service ranks PASS products deterministically; human sales selects the product and approves quotations.

## Responsibility boundary

```text
Groq → RFQ understanding / explanation
Deterministic validation → engineering compliance (PASS/FAIL/UNKNOWN)
Recommendation service → eligible product ranking and transparent reasons
Human Sales → product decision
Quotation engine → commercial calculation from catalog pricing
Human Sales → final approval
```

## Phase guidance

### Implemented in Phase 1

- Repository scaffold
- FastAPI backend foundation
- React frontend shell
- PostgreSQL + pgvector via Docker Compose
- Alembic migrations for organizations, users, organization_members
- Health endpoints
- Initial tests and CI
- Groq-only LLM foundation (`app/llm/`)

### Implemented in Phase 2

- Product catalog models (manufacturers, categories, products, specifications, pricing)
- Read-only catalog APIs under `/api/v1/`
- Idempotent synthetic catalog seed (`python -m app.seed.catalog`)

### Implemented in Phase 3

- RFQ structured requirement extraction via Groq (`POST /api/v1/rfqs/extract`)
- Canonical `SpecKey` reuse with explicit comparison operators

### Implemented in Phase 4

- Deterministic validation service (`app/services/validation.py`) — PASS/FAIL/UNKNOWN
- Unit normalization for voltage, temperature, current, and length
- Validation APIs under `/api/v1/validation/products`

### Implemented in Phase 5A

- Deterministic product recommendation service (`app/services/recommendation.py`)
- Recommendation API under `/api/v1/recommendations/products`
- PASS-only eligibility gate; transparent ranking by evidence, price, and lead time
- Sales Dashboard recommendation step with human sales decision before quotation

### Implemented in Phase 6

- Product datasheet models (`product_documents`, `document_chunks`) with pgvector embeddings
- Deterministic embedding provider (`app/embeddings/`) separate from Groq
- Datasheet ingestion (`app/ingest/`) for PDF and plain-text datasheets
- Semantic retrieval and requirement-linked evidence (`app/services/evidence.py`)
- APIs under `/api/v1/documents/` and `/api/v1/evidence/`
- Demo datasheet seed (`python -m app.seed.documents` after catalog seed)

### Implemented in Phase 7

- Quotation models (`quotations`, `quotation_line_items`) with price snapshots
- Deterministic commercial calculation (`app/services/quotation_calculation.py`)
- Quotation APIs under `/api/v1/quotations` (create, get, list, status update)
- Technical PASS required; FAIL/UNKNOWN blocked at quotation creation

### Implemented in Phase 8

- Sales Dashboard (`frontend/src/features/sales/`) — end-to-end RFQ → quotation workflow
- Primary route `/` and `/sales` orchestrating existing Phase 3–7 APIs
- No new backend intelligence; UX and workflow only

### Implemented in Phase 8.5

- Quotation customer communication drafts (`quotation_communications`)
- Demo-mode email sender (`app/email/`) — records send without external delivery
- Sales follow-up queue (`sales_follow_ups`) with P0/P1/P2 priorities
- APIs under `/api/v1/quotations/{id}/communication`, `/send`, and `/api/v1/sales/follow-ups`
- Sales Dashboard customer email review, explicit send gate, and follow-up panels

### Implemented in Phase 9

- Architecture invariant regression tests (validation authority, PASS-only recommendation/quotation, evidence non-override)
- DemoEmailSender unit tests (no external delivery)
- End-to-end API workflow integration tests (RFQ extract → validation → evidence → recommendation → quotation → communication → send → follow-up)
- Expanded Sales Dashboard frontend workflow, stepper, follow-up, and negative-path tests
- Quotation calculation edge-case tests and API unknown-product guard test
- CEO demo hardening: repeatable deterministic demo data, simulated email disclaimer, duplicate-send protection

### Implemented in Phase 10

- Production Docker images (FastAPI backend, Nginx frontend SPA)
- `docker-compose.prod.yml`, `frontend/nginx.conf.template`, `.dockerignore`
- AWS MVP deployment guide (`docs/aws-mvp-deployment.md`) — ECR, ECS Fargate, ALB, RDS, S3, Secrets Manager, CloudWatch
- ECS task definition examples (`deploy/aws/`)
- CEO packaging docs (presentation, demo script, architecture, limitations, technical decisions)
- Local startup scripts (`scripts/start-local.ps1`, `scripts/reset-demo.ps1`)

### Do not implement yet

- ML-based recommendation models or training
- BOM/proposal generation
- CRM/ERP integration, real SMTP/email provider delivery, payments
- MCP server, plugins, Kubernetes/EKS, Terraform, CI/CD pipelines, HA production infrastructure

Create interfaces or placeholders when useful, but defer feature work.

## Local commands

Migrations must run before seed commands. Seeds do not apply schema changes.

```bash
docker compose up -d postgres redis minio
cd backend && pip install -e ".[dev]"
alembic upgrade head
python -m app.seed.catalog
python -m app.seed.followups
python -m app.seed.documents
uvicorn app.main:app --reload --port 8020
cd frontend && npm install && npm run dev
```

If seeds fail with missing-table errors, run `alembic upgrade head` first. For a disposable local DB reset: `docker compose down -v`, then repeat the steps above.

## Testing expectations

- Backend: `pytest`, `ruff check .`
- Frontend: `npm run test`, `npm run build`, `npm run lint`
- Keep CI green before proposing merges

## Security

- Never commit secrets or `.env`
- Use environment variables for credentials
- Configure Groq with `GROQ_API_KEY`, `GROQ_MODEL`, and `GROQ_BASE_URL` in backend env only
- Never add `GROQ_API_KEY` to frontend `VITE_*` variables
- Treat uploaded RFQ/document content as untrusted input in later phases
