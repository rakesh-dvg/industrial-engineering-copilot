"""Phase 9 end-to-end API workflow integration tests."""

from collections.abc import AsyncGenerator
from datetime import date
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import get_settings
from app.database import get_db_session
from app.embeddings.deps import get_embedding_provider
from app.llm import get_llm_client
from app.llm.groq_client import GroqLLMClient
from app.main import create_app
from app.schemas.rfq import RfqExtractionResult
from app.seed.catalog import seed_catalog
from app.seed.documents import seed_product_datasheets
from tests.test_validation import DEMO_REQUIREMENTS


async def _product_id(client: AsyncClient, model_number: str) -> str:
    response = await client.get("/api/v1/products", params={"model_number": model_number})
    assert response.status_code == 200
    return response.json()["items"][0]["id"]


@pytest_asyncio.fixture
async def integration_client(db_engine) -> AsyncGenerator[AsyncClient, None]:
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False, class_=AsyncSession)
    async with session_factory() as session:
        await seed_catalog(session)
        await seed_product_datasheets(session)

    mock_llm = MagicMock(spec=GroqLLMClient)
    mock_llm.generate_structured_model.return_value = RfqExtractionResult(
        customer_name="ABC Manufacturing",
        customer_reference="RFQ-001",
        title="Industrial Ethernet Switch Quotation",
        quantity=10,
        requirements=DEMO_REQUIREMENTS,
    )

    app = create_app()

    async def override_get_db_session():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_llm_client] = lambda: mock_llm

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
    get_settings.cache_clear()
    get_embedding_provider.cache_clear()


@pytest.mark.asyncio
async def test_ceo_demo_api_chain(integration_client: AsyncClient):
    extract = await integration_client.post(
        "/api/v1/rfqs/extract",
        json={"raw_text": "Customer wants 10 industrial Ethernet switches."},
    )
    assert extract.status_code == 200
    extraction = extract.json()
    assert extraction["customer_name"] == "ABC Manufacturing"
    assert extraction["quantity"] == 10
    assert len(extraction["requirements"]) == 5

    product_ids = []
    for model_number in ("NS-SW-005", "VIS-SW-003", "AC-SW-008"):
        product_ids.append(await _product_id(integration_client, model_number))

    validation = await integration_client.post(
        "/api/v1/validation/products",
        json={
            "product_ids": product_ids,
            "requirements": extraction["requirements"],
        },
    )
    assert validation.status_code == 200
    statuses = {
        item["model_number"]: item["status"] for item in validation.json()["results"]
    }
    assert statuses == {
        "NS-SW-005": "PASS",
        "VIS-SW-003": "FAIL",
        "AC-SW-008": "UNKNOWN",
    }

    evidence = await integration_client.post(
        "/api/v1/evidence/products",
        json={
            "product_ids": product_ids,
            "requirements": extraction["requirements"],
        },
    )
    assert evidence.status_code == 200
    pass_evidence = next(
        item for item in evidence.json()["results"] if item["model_number"] == "NS-SW-005"
    )
    assert pass_evidence["status"] == "PASS"
    assert any(req["evidence_status"] == "found" for req in pass_evidence["requirements"])

    recommendation = await integration_client.post(
        "/api/v1/recommendations/products",
        json={
            "product_ids": product_ids,
            "requirements": extraction["requirements"],
        },
    )
    assert recommendation.status_code == 200
    rec_payload = recommendation.json()
    assert rec_payload["primary_recommendation"]["model_number"] == "NS-SW-005"
    assert rec_payload["primary_recommendation"]["unit_price"] == "185.00"
    assert rec_payload["primary_recommendation"]["lead_time_days"] == 14

    pass_id = await _product_id(integration_client, "NS-SW-005")
    quotation = await integration_client.post(
        "/api/v1/quotations",
        json={
            "customer_name": "ABC Manufacturing",
            "customer_email": "procurement@abcmanufacturing.example",
            "customer_reference": "RFQ-001",
            "title": "Industrial Ethernet Switch Quotation",
            "product_id": pass_id,
            "quantity": 10,
            "discount_percent": "0",
            "validity_days": 30,
            "requirements": extraction["requirements"],
        },
    )
    assert quotation.status_code == 200
    quotation_payload = quotation.json()
    quotation_id = quotation_payload["id"]
    assert quotation_payload["status"] == "DRAFT"
    assert quotation_payload["total"] == "1850.00"

    approved = await integration_client.patch(
        f"/api/v1/quotations/{quotation_id}/status",
        json={"status": "APPROVED"},
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "APPROVED"

    communication = await integration_client.post(
        f"/api/v1/quotations/{quotation_id}/communication",
        json={},
    )
    assert communication.status_code == 200
    comm_payload = communication.json()
    assert comm_payload["status"] == "DRAFT"
    assert comm_payload["demo_mode"] is True
    assert "procurement@abcmanufacturing.example" in comm_payload["customer_email"]

    get_comm = await integration_client.get(
        f"/api/v1/quotations/{quotation_id}/communication",
    )
    assert get_comm.status_code == 200
    assert get_comm.json()["id"] == comm_payload["id"]

    ready = await integration_client.patch(
        f"/api/v1/quotations/{quotation_id}/communication",
        json={"status": "READY_TO_SEND"},
    )
    assert ready.status_code == 200
    assert ready.json()["status"] == "READY_TO_SEND"

    sent = await integration_client.post(f"/api/v1/quotations/{quotation_id}/send")
    assert sent.status_code == 200
    sent_payload = sent.json()
    assert sent_payload["communication"]["status"] == "SENT"
    assert sent_payload["demo_mode"] is True
    assert "no external" in sent_payload["send_detail"].lower()

    follow_ups = await integration_client.get(
        "/api/v1/sales/follow-ups",
        params={"status": "OPEN", "due_date": date.today().isoformat()},
    )
    assert follow_ups.status_code == 200
    assert follow_ups.json()["total"] >= 1
    follow_up_id = follow_ups.json()["items"][0]["id"]
    assert follow_ups.json()["items"][0]["priority"] == "P1"

    completed = await integration_client.patch(
        f"/api/v1/sales/follow-ups/{follow_up_id}",
        json={"status": "COMPLETED"},
    )
    assert completed.status_code == 200
    assert completed.json()["status"] == "COMPLETED"

    open_today = await integration_client.get(
        "/api/v1/sales/follow-ups",
        params={"status": "OPEN", "due_date": date.today().isoformat()},
    )
    assert open_today.json()["total"] == 0

    sent_history = await integration_client.get(
        "/api/v1/sales/follow-ups",
        params={"sent_only": True},
    )
    assert sent_history.status_code == 200
    assert sent_history.json()["total"] >= 1


@pytest.mark.asyncio
async def test_ceo_demo_chain_blocks_fail_and_unknown_quotations(integration_client: AsyncClient):
    requirements = [req.model_dump(mode="json") for req in DEMO_REQUIREMENTS]

    fail_id = await _product_id(integration_client, "VIS-SW-003")
    fail_response = await integration_client.post(
        "/api/v1/quotations",
        json={
            "customer_name": "ABC Manufacturing",
            "product_id": fail_id,
            "quantity": 10,
            "requirements": requirements,
        },
    )
    assert fail_response.status_code == 422
    assert fail_response.json()["error"]["code"] == "QUOTATION_VALIDATION_FAILED"

    unknown_id = await _product_id(integration_client, "AC-SW-008")
    unknown_response = await integration_client.post(
        "/api/v1/quotations",
        json={
            "customer_name": "ABC Manufacturing",
            "product_id": unknown_id,
            "quantity": 10,
            "requirements": requirements,
        },
    )
    assert unknown_response.status_code == 422
    assert unknown_response.json()["error"]["code"] == "QUOTATION_VALIDATION_UNKNOWN"


@pytest.mark.asyncio
async def test_duplicate_send_blocked_in_api_chain(integration_client: AsyncClient):
    pass_id = await _product_id(integration_client, "NS-SW-005")
    requirements = [req.model_dump(mode="json") for req in DEMO_REQUIREMENTS]

    create_response = await integration_client.post(
        "/api/v1/quotations",
        json={
            "customer_name": "ABC Manufacturing",
            "customer_email": "procurement@abcmanufacturing.example",
            "product_id": pass_id,
            "quantity": 10,
            "requirements": requirements,
        },
    )
    quotation_id = create_response.json()["id"]
    await integration_client.patch(
        f"/api/v1/quotations/{quotation_id}/status",
        json={"status": "APPROVED"},
    )
    await integration_client.post(
        f"/api/v1/quotations/{quotation_id}/communication",
        json={},
    )
    await integration_client.patch(
        f"/api/v1/quotations/{quotation_id}/communication",
        json={"status": "READY_TO_SEND"},
    )
    await integration_client.post(f"/api/v1/quotations/{quotation_id}/send")

    follow_ups_before = await integration_client.get(
        "/api/v1/sales/follow-ups",
        params={"sent_only": True},
    )
    total_before = follow_ups_before.json()["total"]

    duplicate = await integration_client.post(f"/api/v1/quotations/{quotation_id}/send")
    assert duplicate.status_code == 422
    assert duplicate.json()["error"]["code"] == "QUOTATION_ALREADY_SENT"

    follow_ups_after = await integration_client.get(
        "/api/v1/sales/follow-ups",
        params={"sent_only": True},
    )
    assert follow_ups_after.json()["total"] == total_before
