import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_health(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "Industrial Engineering Copilot"
    assert "version" in payload
    assert "environment" in payload


@pytest.mark.asyncio
async def test_api_health(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["dependencies"]["database"]["status"] == "ok"


@pytest.mark.asyncio
async def test_cors_allows_local_frontend_origin(client: AsyncClient) -> None:
    response = await client.options(
        "/api/v1/rfqs/extract",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert "POST" in (response.headers.get("access-control-allow-methods") or "")
