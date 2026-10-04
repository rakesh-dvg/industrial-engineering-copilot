# Industrial Engineering Copilot — MCP demo server

Small **stdio MCP server** that exposes safe, read-only demo tools for agents. It does **not** connect to PostgreSQL, Groq, or the FastAPI backend.

## Tools

| Tool | Purpose |
|------|---------|
| `search_products` | Filter in-memory demo catalog |
| `get_product` | Product detail + specifications |
| `validate_requirement` | Deterministic PASS/FAIL/UNKNOWN (subset of spec keys) |
| `create_quote_draft` | Draft commercial total (requires human approval in the real app) |

## Security boundaries

- No API keys, passwords, or `.env` access
- No shell execution or arbitrary filesystem reads
- No network calls
- Sample data only (`NS-SW-005`, `VIS-SW-003`, `AC-SW-008`)

## Run locally

```powershell
cd mcp-server
pip install -e .
iec-mcp
```

## Cursor / MCP client example

```json
{
  "mcpServers": {
    "iec-demo": {
      "command": "iec-mcp",
      "args": []
    }
  }
}
```

For production workflows, agents should call the FastAPI API documented in `openapi.yaml` instead of this demo server.
