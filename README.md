# Industrial Engineering Copilot

**From Engineering Requirements to Product Decisions**

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

Industrial Engineering Copilot helps industrial distributors and automation sales teams turn customer RFQs into validated product recommendations, quotations, and prioritized follow-ups — with deterministic engineering compliance and traceable evidence.

## Business value

Engineering validation and sales execution usually live in separate tools and email threads. This MVP connects them: sales sees which product **passes** the requirements, **why** (specs + evidence), what to **quote**, and which customers need **follow-up today**.

The AI extracts language from RFQs; it does **not** override PASS/FAIL/UNKNOWN decisions.

## Demo

**Customer:** ABC Manufacturing — 10 industrial Ethernet switches (24 VDC, 5+ ports, DIN rail, Modbus TCP, -20°C).

| Product | Validation |
|---------|------------|
| NS-SW-005 | PASS → recommended → Q-2026-0001 @ USD 1,850 |
| VIS-SW-003 | FAIL |
| AC-SW-008 | UNKNOWN |

After simulated email send, **Today's Sales Follow-ups** shows Apex (P0), ABC (P1), and Delta (P2) — Open Quotation Value **USD 14,500**.

Full walkthrough: [docs/CEO-demo-script.md](docs/CEO-demo-script.md)

## Architecture

- **Product design:** [docs/target-architecture.md](docs/target-architecture.md)
- **AWS MVP deployment:** [docs/architecture.md](docs/architecture.md)

## Local startup

**Prerequisites:** Docker, Python 3.12+, Node.js 22+, Groq API key in `.env`

```powershell
cp .env.example .env
.\scripts\start-local.ps1
```

Then in two terminals:

```powershell
# Terminal 1 — backend
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8020

# Terminal 2 — frontend
cd frontend
npm install
npm run dev
```

- Frontend: http://localhost:5173
- API docs: http://localhost:8020/docs

**Migrations before seeds:** `alembic upgrade head` → `python -m app.seed.catalog` → `python -m app.seed.followups` → `python -m app.seed.documents`

Reset local demo data: `.\scripts\reset-demo.ps1`

## AWS MVP deployment

Deploy to AWS for a single public CEO demo URL (ECS Fargate + ALB + RDS + S3):

→ **[docs/aws-mvp-deployment.md](docs/aws-mvp-deployment.md)**

Production Docker files: `backend/Dockerfile`, `frontend/Dockerfile`, `frontend/nginx.conf`, `docker-compose.prod.yml`

## Testing

```powershell
# Backend
cd backend
ruff check .
pytest -q

# Frontend
cd frontend
npm run lint
npm run test
npm run build

# OpenAPI contract
cd ..
python .github/scripts/check_openapi_paths.py
```

## Limitations

MVP scope: simulated email, synthetic demo data, no CRM, no HA/autoscaling on AWS, Groq dependency.

→ [docs/limitations-roadmap.md](docs/limitations-roadmap.md)

## Future roadmap

CRM integration, real email, PDF quotations, enterprise auth, production observability, infrastructure-as-code, autoscaling/HA — see [docs/limitations-roadmap.md](docs/limitations-roadmap.md).

## Related documents

| Document | Purpose |
|----------|---------|
| [docs/CEO-presentation.md](docs/CEO-presentation.md) | Business narrative |
| [docs/CEO-demo-script.md](docs/CEO-demo-script.md) | 3–5 minute demo script |
| [docs/technical-decisions.md](docs/technical-decisions.md) | Why key choices were made |
| [docs/aws-mvp-deployment.md](docs/aws-mvp-deployment.md) | Step-by-step AWS guide |
| [docs/screenshots/README.md](docs/screenshots/README.md) | Manual screenshot checklist |
| [AGENTS.md](AGENTS.md) | Agent/developer instructions |
| [openapi.yaml](openapi.yaml) | API contract |
