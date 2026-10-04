# Agent security

## Least privilege

Agents working on this repository should:

- Read specs (`openapi.yaml`, `AGENTS.md`, `docs/`)
- Propose code changes via PRs with tests
- Use MCP **demo** tools or documented APIs

Agents must **not**:

- Load or echo `.env` / Secrets Manager values
- Run unrestricted shell on production hosts
- Deploy AWS resources (demo infrastructure is decommissioned)
- Disable validation, recommendation, or quotation guards

## Tool restrictions

| Tool class | Policy |
|------------|--------|
| MCP `mcp-server/` | In-memory catalog only |
| FastAPI | Same rules as human users; no bypass headers |
| Git | Never commit secrets; hooks in `agent-hooks/` |
| Database | Use migrations (`alembic`); no ad-hoc prod SQL |

## Approval boundaries

Documented in [docs/permissions.md](../docs/permissions.md):

- Product selection
- Quotation APPROVED
- Customer send (even in demo mode, UI requires explicit action)

## Filesystem

Hooks scan for staged secrets. Agents should not add alternate LLM providers or frontend `VITE_GROQ_*` variables.
