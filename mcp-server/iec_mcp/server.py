"""Stdio MCP server exposing safe, in-memory Industrial Engineering tools."""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from iec_mcp import catalog

mcp = FastMCP(
    "Industrial Engineering Copilot Tools",
    instructions=(
        "Demo tools for RFQ workflows. Uses in-memory sample catalog only. "
        "Does not access databases, secrets, or the filesystem."
    ),
)


@mcp.tool()
def search_products(query: str) -> str:
    """Search demo catalog products by model, name, or manufacturer substring."""
    return json.dumps(catalog.search_products(query), indent=2)


@mcp.tool()
def get_product(model_number: str) -> str:
    """Return one demo product with specifications, or an error payload."""
    product = catalog.get_product(model_number)
    if product is None:
        return json.dumps({"error": "NOT_FOUND", "model_number": model_number})
    return json.dumps(product, indent=2)


@mcp.tool()
def validate_requirement(model_number: str, spec_key: str, operator: str, value: str) -> str:
    """Deterministic PASS/FAIL/UNKNOWN check for a subset of demo spec keys."""
    result = catalog.validate_requirement(model_number, spec_key, operator, value)
    return json.dumps({"model_number": model_number, **result}, indent=2)


@mcp.tool()
def create_quote_draft(model_number: str, quantity: int) -> str:
    """Compute a draft quote total from demo pricing — human approval required."""
    try:
        payload = catalog.create_quote_draft(model_number, quantity)
    except ValueError as exc:
        return json.dumps({"error": str(exc)})
    return json.dumps(payload, indent=2)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
