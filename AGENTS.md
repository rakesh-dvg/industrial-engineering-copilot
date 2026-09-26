# Agent Instructions — Industrial Engineering Copilot

## Project identity

- **Name:** Industrial Engineering Copilot
- **Tagline:** From Engineering Requirements to Product Decisions
- **Architecture source of truth:** `docs/target-architecture.md`
- **API contract:** `openapi.yaml`

## Critical boundary

The adjacent repository `../sai-lee-ai-engineer` is **reference only**.

Do **not** copy or adapt:

- Sai-Lee branding, prompts, DOCX files, logos, or assets
- Old Streamlit application code
- Chroma DB or `sai_lee_docs`
- Synthetic Sai-Lee company/product data

Build a generic greenfield application for this repository.

## Engineering principles

1. **OpenAPI-first** — Update `openapi.yaml` when adding API endpoints.
2. **Deterministic validation** — PASS/FAIL/UNKNOWN for spec checks; never invent specs.
3. **Org scoping** — Every tenant resource must include `organization_id` enforcement.
4. **Evidence traceability** — Recommendations must link to structured specs or document citations.
5. **Minimal diffs** — Match existing conventions; avoid unrelated changes.
6. **Groq-only LLM** — Use the backend Groq client in `app/llm/`. Never add alternate LLM providers or expose `GROQ_API_KEY` to the frontend.
7. **LLM is not the decision engine** — Groq may extract, explain, or draft; deterministic validation must never be overridden by model output.

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

### Do not implement yet

- Product catalog seed data
- RFQ extraction and recommendation pipeline
- Document ingestion, embeddings, semantic search
- BOM/proposal generation
- MCP server, plugins, production deployment

Create interfaces or placeholders when useful, but defer feature work.

## Local commands

```bash
docker compose up -d postgres redis minio
cd backend && pip install -e ".[dev]" && alembic upgrade head && uvicorn app.main:app --reload
cd frontend && npm install && npm run dev
```

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
