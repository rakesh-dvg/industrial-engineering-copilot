# Agent and tool permissions

## Principles

- **Least privilege** — agents get read/search/validate tools, not admin or deploy access.
- **Deterministic authority** — validation and quotation eligibility stay in FastAPI services.
- **Human gates** — send email, approve quotation, select product.

## MCP demo server (`mcp-server/`)

| Permission | Status |
|------------|--------|
| Read in-memory demo catalog | Allowed |
| Compute draft quote totals | Allowed (marked draft) |
| Network to Groq or RDS | Denied |
| Read `.env` or repo secrets | Denied |
| Shell / filesystem | Denied |

## Application API (when agent uses REST)

| Endpoint group | Agent may | Human required |
|----------------|-----------|----------------|
| RFQ extract | Call with user-provided RFQ text | Review extracted requirements |
| Validation / evidence / recommendations | Call | Interpret FAIL/UNKNOWN |
| Quotations | Create draft | Approve status, select product |
| Communication / send | Draft via API | READY_TO_SEND + send |
| Health / catalog read | Call | — |

## Filesystem (Cursor / local agent)

| Path | Access |
|------|--------|
| `openapi.yaml`, `docs/`, source | Read for implementation |
| `.env` | Must not read or commit |
| `deploy/aws/` | Reference only — no live deploy |

## Escalation

Agents must stop and ask a human when:

- Validation returns UNKNOWN for a mandatory spec
- No PASS products exist
- Customer RFQ contains conflicting requirements
- User asks to bypass quotation or send gates

See [security/agent-security.md](../security/agent-security.md) for prohibited actions.
