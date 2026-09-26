# Industrial Engineering Copilot

**From Engineering Requirements to Product Decisions**

Industrial Engineering Copilot is a generic, AI-assisted engineering application for industrial distributors, automation integrators, panel builders, and engineering solution providers.

This repository is a **greenfield** implementation. The adjacent `sai-lee-ai-engineer` project is reference-only and must not be copied into this codebase.

## Phase 1 scope

Phase 1 establishes the project foundation:

- FastAPI backend with versioned API routes
- React + TypeScript frontend shell
- PostgreSQL with pgvector extension
- Redis and MinIO via Docker Compose
- Alembic migrations for organizations, users, and memberships
- OpenAPI contract at `openapi.yaml`
- Health checks and initial automated tests
- GitHub Actions CI
- Groq-only LLM foundation (backend-side; extraction/drafting only)

Product intelligence features (RFQ analysis, recommendations, RAG, BOM, proposals) are intentionally deferred to later phases.

## Groq LLM configuration

This project uses **Groq as its only LLM provider**. The API key is read by the FastAPI backend from environment configuration and must never be committed or exposed to the frontend.

Add these values to your local `.env` (see `.env.example`):

```text
GROQ_API_KEY=your-groq-api-key
GROQ_MODEL=openai/gpt-oss-120b
GROQ_BASE_URL=https://api.groq.com/openai/v1
```

Default model: `openai/gpt-oss-120b`

Architecture:

```text
React frontend -> FastAPI backend -> Groq API
```

The browser never receives `GROQ_API_KEY`. Do not add Groq settings to any `VITE_*` variable.

Groq is used only for language tasks such as extraction, explanation, and drafting. Deterministic engineering validation (PASS/FAIL/UNKNOWN) remains outside the LLM layer.

## Architecture

See [docs/target-architecture.md](docs/target-architecture.md) for the authoritative design.

## Prerequisites

- Docker and Docker Compose
- Python 3.12+
- Node.js 22+

## Quick start

### 1. Configure environment

```bash
cp .env.example .env
```

### 2. Start infrastructure

```bash
docker compose up -d postgres redis minio
```

### 3. Backend setup

```bash
cd backend
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Frontend setup

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open:

- Frontend: http://localhost:5173
- API docs: http://localhost:8000/docs
- OpenAPI JSON: http://localhost:8000/openapi.json

## Full stack with Docker Compose

```bash
docker compose up --build
```

This starts PostgreSQL, Redis, MinIO, backend, and frontend.

## Testing

### Backend

Ensure PostgreSQL is running, then:

```bash
cd backend
pip install -e ".[dev]"

# Optional: create a dedicated test database
# docker exec -it iec-postgres psql -U iec -d iec -c "CREATE DATABASE iec_test;"

pytest
ruff check .
```

### Frontend

```bash
cd frontend
npm install
npm run test
npm run build
npm run lint
```

## API contract

The repository-level OpenAPI contract lives at [openapi.yaml](openapi.yaml). FastAPI exposes a generated schema at `/openapi.json`. Keep the contract aligned as endpoints are added in later phases.

## Project structure

```text
backend/          FastAPI application, Alembic, tests
frontend/         React + Vite SPA
docs/             Architecture and design documents
openapi.yaml      API contract (OpenAPI 3.1)
docker-compose.yml
.github/workflows/ci.yml
```

## Related documents

- [docs/target-architecture.md](docs/target-architecture.md)
- [product-spec.md](product-spec.md)
- [AGENTS.md](AGENTS.md)
