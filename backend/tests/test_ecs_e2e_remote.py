"""Optional live ECS workflow smoke test.

Set ECS_E2E_BASE_URL (e.g. http://3.108.225.134:8000) to run against deployed backend.
Skipped when unset — no secrets required.
"""

import os

import httpx
import pytest

DEMO_RFQ = """Customer: ABC Manufacturing

Please quote 10 industrial Ethernet switches.

Requirements:
- 24 VDC power
- minimum 5 Ethernet ports
- DIN rail mounting
- Modbus TCP support
- operating temperature down to -20°C"""

DEMO_SWITCH_MODELS = ["NS-SW-005", "VIS-SW-003", "AC-SW-008"]

BASE_URL = os.getenv("ECS_E2E_BASE_URL", "").strip()


pytestmark = pytest.mark.skipif(not BASE_URL, reason="ECS_E2E_BASE_URL not set")


@pytest.fixture(scope="module")
def ecs_client() -> httpx.Client:
    with httpx.Client(base_url=BASE_URL, timeout=120.0) as client:
        yield client


def test_ecs_health(ecs_client: httpx.Client) -> None:
    response = ecs_client.get("/health")
    assert response.status_code == 200


def test_ecs_full_demo_chain(ecs_client: httpx.Client) -> None:
    extract = ecs_client.post("/api/v1/rfqs/extract", json={"raw_text": DEMO_RFQ})
    assert extract.status_code == 200, extract.text[:500]
    extraction = extract.json()
    assert extraction.get("customer_name") == "ABC Manufacturing"
    assert extraction.get("quantity") == 10
    requirements = extraction["requirements"]
    assert len(requirements) >= 5

    catalog = ecs_client.get("/api/v1/products")
    assert catalog.status_code == 200
    product_ids = [
        item["id"]
        for item in catalog.json()["items"]
        if item["model_number"] in DEMO_SWITCH_MODELS
    ]
    assert len(product_ids) == 3

    payload = {"product_ids": product_ids, "requirements": requirements}
    validation = ecs_client.post("/api/v1/validation/products", json=payload)
    assert validation.status_code == 200
    statuses = {r["model_number"]: r["status"] for r in validation.json()["results"]}
    assert statuses["NS-SW-005"] == "PASS"
    assert statuses["VIS-SW-003"] == "FAIL"
    assert statuses["AC-SW-008"] == "UNKNOWN"

    recommendation = ecs_client.post("/api/v1/recommendations/products", json=payload)
    assert recommendation.status_code == 200
    primary = recommendation.json().get("primary_recommendation")
    assert primary is not None
    assert primary["model_number"] == "NS-SW-005"

    quote = ecs_client.post(
        "/api/v1/quotations",
        json={
            "customer_name": "ABC Manufacturing",
            "customer_email": "procurement@abcmanufacturing.example",
            "product_id": primary["product_id"],
            "quantity": 10,
            "discount_percent": "0",
            "validity_days": 30,
            "requirements": requirements,
        },
    )
    assert quote.status_code == 200, quote.text[:500]
    quotation_id = quote.json()["id"]

    approved = ecs_client.patch(
        f"/api/v1/quotations/{quotation_id}/status",
        json={"status": "APPROVED"},
    )
    assert approved.status_code == 200

    comm = ecs_client.post(
        f"/api/v1/quotations/{quotation_id}/communication",
        json={"customer_email": "procurement@abcmanufacturing.example"},
    )
    assert comm.status_code == 200

    ready = ecs_client.patch(
        f"/api/v1/quotations/{quotation_id}/communication",
        json={"status": "READY_TO_SEND"},
    )
    assert ready.status_code == 200

    sent = ecs_client.post(f"/api/v1/quotations/{quotation_id}/send")
    assert sent.status_code == 200
    assert sent.json()["communication"]["status"] == "SENT"

    follow_ups = ecs_client.get(
        "/api/v1/sales/follow-ups",
        params={"sent_only": True},
    )
    assert follow_ups.status_code == 200
    assert follow_ups.json()["total"] >= 1
