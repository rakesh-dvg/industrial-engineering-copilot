# Agent extension pack (Module 5)

Lightweight artifacts showing how an **Industrial Engineering RFQ Specialist** agent can work safely with this application.

## Flow

```text
Capability (rfq-specialist.md)
        ↓
Custom agent (custom-agent/rfq-specialist-agent.md)
        ↓
Tools — MCP demo server OR FastAPI (openapi.yaml)
        ↓
Hooks — pre-commit / pre-deploy validation
        ↓
Human approval — product, quotation, send
        ↓
Application API — deterministic validation & pricing
```

## Repository layout

| Path | Purpose |
|------|---------|
| [agent-capabilities/rfq-specialist.md](../agent-capabilities/rfq-specialist.md) | Role, inputs/outputs, limits |
| [custom-agent/rfq-specialist-agent.md](../custom-agent/rfq-specialist-agent.md) | Agent instructions and refusal rules |
| [mcp-server/](../mcp-server/) | Stdio MCP tools on in-memory demo catalog |
| [agent-hooks/](../agent-hooks/) | PowerShell validation hooks |
| [docs/permissions.md](permissions.md) | Tool and data permissions |

## Example: customer RFQ to quotation

```text
Customer RFQ email
    ↓
RFQ Specialist Agent
    ↓
POST /api/v1/rfqs/extract  (Groq — language only)
    ↓
POST /api/v1/validation/products  (deterministic PASS/FAIL/UNKNOWN)
    ↓
POST /api/v1/evidence/products  (RAG citations)
    ↓
POST /api/v1/recommendations/products  (PASS-only rank)
    ↓
Human sales selects NS-SW-005
    ↓
POST /api/v1/quotations → PATCH status APPROVED
    ↓
POST /communication → PATCH READY_TO_SEND → POST /send (demo)
    ↓
GET /api/v1/sales/follow-ups
```

Offline agents can use MCP tools `search_products` and `validate_requirement` for training demos without a running backend.

## MCP server quick start

```powershell
cd mcp-server
pip install -e .
iec-mcp
```

See [mcp-server/README.md](../mcp-server/README.md).

## Hooks

```powershell
.\agent-hooks\pre-commit-security-check.ps1
.\agent-hooks\pre-deploy-validation.ps1
```
