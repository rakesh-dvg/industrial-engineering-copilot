# Industrial Engineering Copilot

**From Engineering Requirements to Product Decisions**

Final project for the [2026 AI Dev Tools Zoomcamp](https://github.com/rakesh-dvg/industrial-engineering-copilot) (DataTalks.Club).

## Problem and users

Industrial distributors and automation **sales engineers** receive unstructured customer RFQs (email, PDF, portal). Translating language into specs, proving compliance, quoting, and following up is slow and hard to audit.

**Target users:** sales engineers, application engineers, technical reviewers.

**Business value:** One workflow from RFQ → validated recommendation → quotation → simulated customer communication → prioritized follow-ups, with **deterministic PASS/FAIL/UNKNOWN** engineering checks.

**AI role:** Groq extracts requirements and drafts communication text. It does **not** override validation, recommendations, or pricing.

**System boundary:**

```text
Groq → language (extract / draft)
Deterministic services → compliance, ranking, quotation math
Human sales → product choice, approval, send
```

**Example workflow:** Customer ABC requests 10 industrial Ethernet switches (24 VDC, 5+ ports, DIN rail, Modbus TCP, -20°C). NS-SW-005 **PASS** → recommended → quotation → demo email → P1 follow-up. VIS-SW-003 **FAIL**, AC-SW-008 **UNKNOWN**.

## What it does

```text
Customer RFQ
→ Requirements (Groq extraction)
→ Validation (PASS / FAIL / UNKNOWN)
→ Evidence (datasheet RAG)
→ Recommendation (deterministic ranking)
→ Quotation (commercial calculation)
→ Customer communication (simulated send)
→ Sales follow-up queue (P0 / P1 / P2)
```

## Demo

| Product | Validation |
|---------|------------|
| NS-SW-005 | PASS → recommended → Q-2026-0001 @ USD 1,850 |
| VIS-SW-003 | FAIL |
| AC-SW-008 | UNKNOWN |

Walkthrough: [docs/CEO-demo-script.md](docs/CEO-demo-script.md)

## Architecture

**Local (current):**

```text
React/Vite → FastAPI → SQLAlchemy → PostgreSQL
FastAPI → Groq LLM (backend only)
```

**Production-like local stack:** React build → **Nginx** (`frontend/nginx.conf.template`) → FastAPI.

| Topic | Document |
|-------|----------|
| Logical product architecture | [docs/target-architecture.md](docs/target-architecture.md) |
| Local + historical AWS diagrams | [docs/architecture.md](docs/architecture.md) |
| Database & migrations | [docs/database.md](docs/database.md) |
| API contract | [openapi.yaml](openapi.yaml) |

> **AWS infrastructure used for the demonstration has been decommissioned.** The repository is reproducible locally with Docker Compose. Historical AWS steps: [docs/aws-mvp-deployment.md](docs/aws-mvp-deployment.md), [docs/deployment.md](docs/deployment.md).

## Reproducibility (fresh clone)

1. Clone the repository
2. Copy environment template: `cp .env.example .env` (set `GROQ_API_KEY` for live RFQ extract)
3. Install prerequisites: Docker, Python 3.12+, Node.js 22+
4. Start infrastructure: `docker compose up -d postgres redis minio`
5. Backend setup:

   ```powershell
   cd backend
   pip install -e ".[dev]"
   alembic upgrade head
   python -m app.seed.catalog
   python -m app.seed.followups
   python -m app.seed.documents
   uvicorn app.main:app --reload --port 8020
   ```

6. Frontend: `cd frontend && npm install && npm run dev`
7. Open http://localhost:5173 — API http://localhost:8020/docs
8. Run tests (see [docs/testing.md](docs/testing.md))

Shortcut: `.\scripts\start-local.ps1` · Reset demo data: `.\scripts\reset-demo.ps1`

**All-in Docker (dev):** `docker compose up --build` (frontend on http://localhost:5174).

**Prod-like compose:** `docker compose -f docker-compose.prod.yml up --build` (http://localhost:8080).

Container files: `backend/Dockerfile`, `frontend/Dockerfile`, `frontend/nginx.conf.template`, `docker-compose.yml`, `docker-compose.prod.yml`.

## Testing

```powershell
# Backend (PostgreSQL must be running)
cd backend
ruff check .
pytest -q

# Frontend — 27 tests
cd frontend
npm run lint
npm run test
npm run build

# OpenAPI contract
python .github/scripts/check_openapi_paths.py
```

Details: [docs/testing.md](docs/testing.md) · CI: [docs/cicd.md](docs/cicd.md)

## AI-assisted development & agent extension pack

| Document | Purpose |
|----------|---------|
| [docs/ai-assisted-development.md](docs/ai-assisted-development.md) | How AI assistants built and debugged the project |
| [docs/agent-extension-pack.md](docs/agent-extension-pack.md) | Module 5 — capabilities, MCP, hooks, custom agent |
| [AGENTS.md](AGENTS.md) | Ongoing developer/agent instructions |

Artifacts: `agent-capabilities/`, `agent-hooks/`, `mcp-server/`, `custom-agent/`

## Security and operations

[security/](security/) · [ops/](ops/) · [docs/permissions.md](docs/permissions.md)

## Project rubric coverage

| Rubric area | Primary evidence |
|-------------|------------------|
| Problem | This README + `product-spec.md` |
| AI workflow | `docs/ai-assisted-development.md` |
| Architecture | `docs/architecture.md` |
| Frontend | `frontend/src/features/sales/` |
| API | `openapi.yaml` |
| Backend | `backend/app/` |
| Database | `backend/alembic/` |
| Containers | Dockerfiles + Compose |
| Integration testing | `docs/testing.md` |
| Deployment | `docs/deployment.md` (AWS historical) |
| CI/CD | `.github/workflows/ci.yml` |
| Agent extension | `agent-capabilities/`, `mcp-server/`, `custom-agent/` |
| Security/Ops | `security/`, `ops/` |
| Reproducibility | README + `.env.example` |

Full checklist: [docs/final-rubric-checklist.md](docs/final-rubric-checklist.md)

## Documentation index

| Document | Purpose |
|----------|---------|
| [docs/CEO-presentation.md](docs/CEO-presentation.md) | Business narrative |
| [docs/CEO-demo-script.md](docs/CEO-demo-script.md) | Demo script |
| [docs/technical-decisions.md](docs/technical-decisions.md) | Key technical choices |
| [docs/limitations-roadmap.md](docs/limitations-roadmap.md) | MVP limits and roadmap |
| [docs/screenshots/README.md](docs/screenshots/README.md) | Screenshot checklist |

## Limitations

Simulated email, synthetic catalog, Groq dependency, no CRM/HA. See [docs/limitations-roadmap.md](docs/limitations-roadmap.md).
