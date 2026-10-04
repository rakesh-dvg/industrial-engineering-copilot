"""Phase 8.5 quotation communication and follow-up tests."""

from datetime import date

import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.product import Product
from app.models.quotation import QuotationStatus
from app.models.sales_follow_up import FollowUpStatus
from app.schemas.communication import (
    CreateQuotationCommunicationRequest,
    UpdateQuotationCommunicationRequest,
)
from app.schemas.followup import UpdateSalesFollowUpRequest
from app.schemas.quotation import CreateQuotationRequest
from app.seed.catalog import seed_catalog
from app.services.quotation_communication import (
    create_quotation_communication,
    send_quotation_to_customer,
    update_quotation_communication,
)
from app.services.quotations import create_quotation, update_quotation_status
from app.services.sales_followups import list_follow_ups, update_follow_up
from tests.test_validation import DEMO_REQUIREMENTS

DEFAULT_EMAIL = "procurement@abcmanufacturing.example"


async def _approved_quotation(
    db_session,
    *,
    customer_email: str | None = DEFAULT_EMAIL,
):
    await seed_catalog(db_session)
    product = await db_session.scalar(
        select(Product)
        .options(selectinload(Product.specifications), selectinload(Product.pricing))
        .where(Product.model_number == "NS-SW-005"),
    )
    assert product is not None
    created = await create_quotation(
        db_session,
        CreateQuotationRequest(
            customer_name="ABC Manufacturing",
            customer_email=customer_email,
            customer_reference="RFQ-001",
            title="Industrial Ethernet Switches",
            product_id=product.id,
            quantity=10,
            requirements=DEMO_REQUIREMENTS,
        ),
        embedder=None,
    )
    return await update_quotation_status(db_session, created.id, QuotationStatus.APPROVED)


@pytest.mark.asyncio
async def test_communication_created_with_email_draft(db_session):
    quotation = await _approved_quotation(db_session)
    communication = await create_quotation_communication(
        db_session,
        quotation.id,
        request=_request(),
    )

    assert communication.customer_email == "procurement@abcmanufacturing.example"
    assert communication.subject.startswith(f"Quotation {quotation.quotation_number}")
    assert "ABC Manufacturing" in communication.body
    assert "USD 1,850.00" in communication.body
    assert communication.status.value == "DRAFT"


def _request() -> CreateQuotationCommunicationRequest:
    return CreateQuotationCommunicationRequest()


@pytest.mark.asyncio
async def test_email_body_editable(db_session):
    quotation = await _approved_quotation(db_session)
    await create_quotation_communication(db_session, quotation.id, request=_request())
    updated = await update_quotation_communication(
        db_session,
        quotation.id,
        UpdateQuotationCommunicationRequest(body="Updated customer email body."),
    )
    assert updated.body == "Updated customer email body."


@pytest.mark.asyncio
async def test_unapproved_quotation_cannot_create_communication(db_session):
    await seed_catalog(db_session)
    product = await db_session.scalar(
        select(Product)
        .options(selectinload(Product.specifications), selectinload(Product.pricing))
        .where(Product.model_number == "NS-SW-005"),
    )
    assert product is not None
    created = await create_quotation(
        db_session,
        CreateQuotationRequest(
            customer_name="ABC Manufacturing",
            product_id=product.id,
            quantity=10,
            requirements=DEMO_REQUIREMENTS,
        ),
        embedder=None,
    )
    with pytest.raises(HTTPException) as exc_info:
        await create_quotation_communication(db_session, created.id, request=_request())
    assert exc_info.value.status_code == 422


@pytest.mark.asyncio
async def test_approved_quotation_can_be_sent(db_session):
    quotation = await _approved_quotation(db_session)
    await create_quotation_communication(db_session, quotation.id, request=_request())
    result = await send_quotation_to_customer(db_session, quotation.id)

    assert result.communication.status.value == "SENT"
    assert result.communication.sent_at is not None
    assert result.demo_mode is True
    assert "Demo mode" in result.send_detail


@pytest.mark.asyncio
async def test_unsaved_communication_cannot_be_sent(db_session):
    quotation = await _approved_quotation(db_session)
    with pytest.raises(HTTPException) as exc_info:
        await send_quotation_to_customer(db_session, quotation.id)
    assert exc_info.value.detail["error"]["code"] == "COMMUNICATION_NOT_FOUND"


@pytest.mark.asyncio
async def test_duplicate_send_blocked(db_session):
    quotation = await _approved_quotation(db_session)
    await create_quotation_communication(db_session, quotation.id, request=_request())
    await send_quotation_to_customer(db_session, quotation.id)

    with pytest.raises(HTTPException) as exc_info:
        await send_quotation_to_customer(db_session, quotation.id)
    assert exc_info.value.detail["error"]["code"] == "QUOTATION_ALREADY_SENT"


@pytest.mark.asyncio
async def test_follow_up_created_after_send(db_session):
    quotation = await _approved_quotation(db_session)
    await create_quotation_communication(db_session, quotation.id, request=_request())
    await send_quotation_to_customer(db_session, quotation.id)

    follow_ups = await list_follow_ups(db_session, sent_only=True)
    assert follow_ups.total == 1
    item = follow_ups.items[0]
    assert item.customer_name == "ABC Manufacturing"
    assert item.priority.value == "P1"
    assert item.status.value == "OPEN"
    assert item.follow_up_date == date.today()


@pytest.mark.asyncio
async def test_priority_can_be_changed(db_session):
    quotation = await _approved_quotation(db_session)
    await create_quotation_communication(db_session, quotation.id, request=_request())
    await send_quotation_to_customer(db_session, quotation.id)
    follow_up = (await list_follow_ups(db_session, sent_only=True)).items[0]

    updated = await update_follow_up(
        db_session,
        follow_up.id,
        UpdateSalesFollowUpRequest(priority="P0"),
    )
    assert updated.priority.value == "P0"


@pytest.mark.asyncio
async def test_completed_follow_up_excluded_from_today_open_queue(db_session):
    quotation = await _approved_quotation(db_session)
    await create_quotation_communication(db_session, quotation.id, request=_request())
    await send_quotation_to_customer(db_session, quotation.id)
    follow_up = (await list_follow_ups(db_session, sent_only=True)).items[0]
    await update_follow_up(
        db_session,
        follow_up.id,
        UpdateSalesFollowUpRequest(status="COMPLETED"),
    )

    open_today = await list_follow_ups(
        db_session,
        status_filter=FollowUpStatus.OPEN,
        due_date=date.today(),
    )
    assert open_today.total == 0

    sent = await list_follow_ups(db_session, sent_only=True)
    assert sent.total == 1
    assert sent.items[0].status.value == "COMPLETED"


@pytest.mark.asyncio
async def test_fail_quotation_cannot_be_sent(db_session):
    await seed_catalog(db_session)
    product = await db_session.scalar(
        select(Product)
        .options(selectinload(Product.specifications), selectinload(Product.pricing))
        .where(Product.model_number == "VIS-SW-003"),
    )
    assert product is not None

    with pytest.raises(HTTPException):
        await create_quotation(
            db_session,
            CreateQuotationRequest(
                customer_name="ABC Manufacturing",
                product_id=product.id,
                quantity=10,
                requirements=DEMO_REQUIREMENTS,
            ),
            embedder=None,
        )


@pytest.mark.asyncio
async def test_communication_api_flow(seeded_client):
    products = await seeded_client.get("/api/v1/products", params={"model_number": "NS-SW-005"})
    product_id = products.json()["items"][0]["id"]

    create_response = await seeded_client.post(
        "/api/v1/quotations",
        json={
            "customer_name": "ABC Manufacturing",
            "customer_email": "procurement@abcmanufacturing.example",
            "product_id": product_id,
            "quantity": 10,
            "requirements": [req.model_dump(mode="json") for req in DEMO_REQUIREMENTS],
        },
    )
    quotation_id = create_response.json()["id"]
    await seeded_client.patch(
        f"/api/v1/quotations/{quotation_id}/status",
        json={"status": "APPROVED"},
    )

    communication = await seeded_client.post(
        f"/api/v1/quotations/{quotation_id}/communication",
        json={},
    )
    assert communication.status_code == 200
    assert communication.json()["status"] == "DRAFT"

    ready = await seeded_client.patch(
        f"/api/v1/quotations/{quotation_id}/communication",
        json={"status": "READY_TO_SEND"},
    )
    assert ready.status_code == 200
    assert ready.json()["status"] == "READY_TO_SEND"

    sent = await seeded_client.post(f"/api/v1/quotations/{quotation_id}/send")
    assert sent.status_code == 200
    assert sent.json()["communication"]["status"] == "SENT"

    duplicate = await seeded_client.post(f"/api/v1/quotations/{quotation_id}/send")
    assert duplicate.status_code == 422
    assert duplicate.json()["error"]["code"] == "QUOTATION_ALREADY_SENT"

    follow_ups = await seeded_client.get(
        "/api/v1/sales/follow-ups",
        params={"status": "OPEN", "due_date": date.today().isoformat()},
    )
    assert follow_ups.status_code == 200
    assert follow_ups.json()["total"] >= 1

    invalid_priority = await seeded_client.patch(
        f"/api/v1/sales/follow-ups/{follow_ups.json()['items'][0]['id']}",
        json={"priority": "P9"},
    )
    assert invalid_priority.status_code == 422

    completed = await seeded_client.patch(
        f"/api/v1/sales/follow-ups/{follow_ups.json()['items'][0]['id']}",
        json={"status": "COMPLETED"},
    )
    assert completed.status_code == 200
    assert completed.json()["status"] == "COMPLETED"

    open_today = await seeded_client.get(
        "/api/v1/sales/follow-ups",
        params={"status": "OPEN", "due_date": date.today().isoformat()},
    )
    assert open_today.json()["total"] == 0


@pytest.mark.asyncio
async def test_get_communication_api(seeded_client):
    products = await seeded_client.get("/api/v1/products", params={"model_number": "NS-SW-005"})
    product_id = products.json()["items"][0]["id"]
    create_response = await seeded_client.post(
        "/api/v1/quotations",
        json={
            "customer_name": "ABC Manufacturing",
            "customer_email": "procurement@abcmanufacturing.example",
            "product_id": product_id,
            "quantity": 10,
            "requirements": [req.model_dump(mode="json") for req in DEMO_REQUIREMENTS],
        },
    )
    quotation_id = create_response.json()["id"]
    await seeded_client.patch(
        f"/api/v1/quotations/{quotation_id}/status",
        json={"status": "APPROVED"},
    )
    created = await seeded_client.post(
        f"/api/v1/quotations/{quotation_id}/communication",
        json={},
    )
    assert created.status_code == 200

    fetched = await seeded_client.get(f"/api/v1/quotations/{quotation_id}/communication")
    assert fetched.status_code == 200
    assert fetched.json()["customer_email"] == "procurement@abcmanufacturing.example"
    assert fetched.json()["demo_mode"] is True
