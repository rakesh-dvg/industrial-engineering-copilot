# Final rubric checklist (2026 AI Dev Tools Zoomcamp)

| Criterion | Status | Evidence |
| --------- | ------ | -------- |
| 1 Problem | PASS | [README](../README.md), [product-spec.md](../product-spec.md) |
| 2 AI workflow | PASS | [docs/ai-assisted-development.md](ai-assisted-development.md) |
| 3 Architecture | PASS | [docs/architecture.md](architecture.md), [docs/target-architecture.md](target-architecture.md) |
| 4 Frontend | PASS | [frontend/](../frontend/) — Vitest (27 tests) |
| 5 API | PASS | [openapi.yaml](../openapi.yaml), CI OpenAPI job |
| 6 Backend | PASS | [backend/](../backend/) — pytest, FastAPI routers |
| 7 Database | PASS | [backend/alembic/](../backend/alembic/), [docs/database.md](database.md) |
| 8 Containers | PASS | Dockerfiles, `docker-compose.yml`, `frontend/nginx.conf.template` |
| 9 Integration | PASS | [docs/testing.md](testing.md), `tests/test_integration_workflow.py` |
| 10 Deployment | PASS | [docs/deployment.md](deployment.md), [docs/aws-mvp-deployment.md](aws-mvp-deployment.md) (historical) |
| 11 CI/CD | PASS | [.github/workflows/ci.yml](../.github/workflows/ci.yml), [docs/cicd.md](cicd.md) |
| 12 Agent Extension | PASS | [agent-capabilities/](../agent-capabilities/), [mcp-server/](../mcp-server/), [custom-agent/](../custom-agent/), [docs/agent-extension-pack.md](agent-extension-pack.md) |
| 13 Security/Ops | PASS | [security/](../security/), [ops/](../ops/) |
| 14 Reproducibility | PASS | [README](../README.md), [.env.example](../.env.example) |

## Notes for reviewers

- **AWS is not running** — local Docker Compose is the supported path.
- **Groq API key** is optional for CI; RFQ extract tests mock the LLM.
- Migration integration tests may require Linux CI or `psycopg[binary]` on Windows.
