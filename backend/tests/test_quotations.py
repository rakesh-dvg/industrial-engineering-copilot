"""Phase 7 quotation generator tests."""

from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.product import Product
from app.models.product_pricing import ProductPricing
from app.schemas.quotation import CreateQuotationRequest
from app.schemas.validation import ValidationStatus
from app.seed.catalog import seed_catalog
from app.services.quotation_calculation import calculate_line, calculate_quotation
from app.services.quotations import create_quotation, get_quotation
from tests.test_validation import DEMO_REQUIREMENTS


def test_line_calculation_without_discount():
    line = calculate_line(10, Decimal("185.00"), Decimal("0"))
    assert line.line_subtotal == Decimal("1850.00")
    assert line.discount_amount == Decimal("0.00")
    assert line.line_total == Decimal("1850.00")


def test_line_calculation_with_discount():
    line = calculate_line(10, Decimal("185.00"), Decimal("10"))
    assert line.line_subtotal == Decimal("1850.00")
    assert line.discount_amount == Decimal("185.00")
    assert line.line_total == Decimal("1665.00")


def test_quotation_total_aggregation():
    lines = [
        calculate_line(10, Decimal("185.00"), Decimal("0")),
        calculate_line(2, Decimal("145.00"), Decimal("5")),
    ]
    totals = calculate_quotation(lines)
    assert totals.subtotal == Decimal("2140.00")
    assert totals.discount_amount == Decimal("14.50")
    assert totals.total == Decimal("2125.50")


def test_line_calculation_rounding_half_up():
    line = calculate_line(3, Decimal("10.005"), Decimal("0"))
    assert line.line_subtotal == Decimal("30.02")
    assert line.line_total == Decimal("30.02")


def test_line_calculation_rejects_zero_quantity():
    with pytest.raises(ValueError, match="Quantity must be greater than zero"):
        calculate_line(0, Decimal("185.00"), Decimal("0"))


@pytest.mark.asyncio
async def test_create_quotation_ceo_demo(db_session):
    await seed_catalog(db_session)
    product = await db_session.scalar(
        select(Product)
        .options(selectinload(Product.specifications), selectinload(Product.pricing))
        .where(Product.model_number == "NS-SW-005"),
    )
    assert product is not None

    request = CreateQuotationRequest(
        customer_name="ABC Manufacturing",
        customer_reference="RFQ-001",
        title="Industrial Ethernet Switch Quotation",
        product_id=product.id,
        quantity=10,
        discount_percent=Decimal("0"),
        validity_days=30,
        requirements=DEMO_REQUIREMENTS,
    )
    result = await create_quotation(db_session, request, embedder=None)

    assert result.quotation_number.startswith("Q-")
    assert result.status.value == "DRAFT"
    assert result.technical_status == ValidationStatus.PASS
    assert result.currency == "USD"
    assert result.lead_time_days == 14
    assert result.lines[0].unit_price == Decimal("185.00")
    assert result.lines[0].line_total == Decimal("1850.00")
    assert result.total == Decimal("1850.00")
    assert result.validation_snapshot["model_number"] == "NS-SW-005"


@pytest.mark.asyncio
async def test_price_snapshot_preserved_after_catalog_change(db_session):
    await seed_catalog(db_session)
    product = await db_session.scalar(
        select(Product)
        .options(selectinload(Product.specifications), selectinload(Product.pricing))
        .where(Product.model_number == "NS-SW-005"),
    )
    assert product is not None

    request = CreateQuotationRequest(
        customer_name="ABC Manufacturing",
        product_id=product.id,
        quantity=10,
        requirements=DEMO_REQUIREMENTS,
    )
    created = await create_quotation(db_session, request, embedder=None)

    pricing = await db_session.scalar(
        select(ProductPricing).where(ProductPricing.product_id == product.id),
    )
    assert pricing is not None
    pricing.unit_price = Decimal("999.00")
    await db_session.commit()

    stored = await get_quotation(db_session, created.id)
    assert stored.lines[0].unit_price == Decimal("185.00")
    assert stored.total == Decimal("1850.00")


@pytest.mark.asyncio
async def test_fail_product_blocked(db_session):
    await seed_catalog(db_session)
    product = await db_session.scalar(
        select(Product)
        .options(selectinload(Product.specifications), selectinload(Product.pricing))
        .where(Product.model_number == "VIS-SW-003"),
    )
    assert product is not None

    request = CreateQuotationRequest(
        customer_name="ABC Manufacturing",
        product_id=product.id,
        quantity=10,
        requirements=DEMO_REQUIREMENTS,
    )
    with pytest.raises(HTTPException) as exc_info:
        await create_quotation(db_session, request, embedder=None)
    assert exc_info.value.status_code == 422
    assert exc_info.value.detail["error"]["code"] == "QUOTATION_VALIDATION_FAILED"


@pytest.mark.asyncio
async def test_unknown_product_blocked(db_session):
    await seed_catalog(db_session)
    product = await db_session.scalar(
        select(Product)
        .options(selectinload(Product.specifications), selectinload(Product.pricing))
        .where(Product.model_number == "AC-SW-008"),
    )
    assert product is not None

    request = CreateQuotationRequest(
        customer_name="ABC Manufacturing",
        product_id=product.id,
        quantity=10,
        requirements=DEMO_REQUIREMENTS,
    )
    with pytest.raises(HTTPException) as exc_info:
        await create_quotation(db_session, request, embedder=None)
    assert exc_info.value.status_code == 422
    assert exc_info.value.detail["error"]["code"] == "QUOTATION_VALIDATION_UNKNOWN"


@pytest.mark.asyncio
async def test_quotation_number_uniqueness(db_session):
    await seed_catalog(db_session)
    product = await db_session.scalar(
        select(Product)
        .options(selectinload(Product.specifications), selectinload(Product.pricing))
        .where(Product.model_number == "NS-SW-005"),
    )
    assert product is not None

    request = CreateQuotationRequest(
        customer_name="ABC Manufacturing",
        product_id=product.id,
        quantity=1,
        requirements=DEMO_REQUIREMENTS,
    )
    first = await create_quotation(db_session, request, embedder=None)
    second = await create_quotation(db_session, request, embedder=None)
    assert first.quotation_number != second.quotation_number


@pytest.mark.asyncio
async def test_quotation_api_create_and_list(seeded_client):
    products = await seeded_client.get("/api/v1/products", params={"model_number": "NS-SW-005"})
    product_id = products.json()["items"][0]["id"]

    create_response = await seeded_client.post(
        "/api/v1/quotations",
        json={
            "customer_name": "ABC Manufacturing",
            "customer_reference": "RFQ-001",
            "title": "Industrial Ethernet Switch Quotation",
            "product_id": product_id,
            "quantity": 10,
            "discount_percent": "0",
            "validity_days": 30,
            "requirements": [req.model_dump(mode="json") for req in DEMO_REQUIREMENTS],
        },
    )
    assert create_response.status_code == 200
    payload = create_response.json()
    assert payload["technical_status"] == "PASS"
    assert payload["total"] == "1850.00"
    assert payload["status"] == "DRAFT"

    get_response = await seeded_client.get(f"/api/v1/quotations/{payload['id']}")
    assert get_response.status_code == 200

    list_response = await seeded_client.get("/api/v1/quotations")
    assert list_response.status_code == 200
    assert list_response.json()["total"] >= 1


@pytest.mark.asyncio
async def test_quotation_api_validation_unknown(seeded_client):
    products = await seeded_client.get("/api/v1/products", params={"model_number": "AC-SW-008"})
    product_id = products.json()["items"][0]["id"]

    response = await seeded_client.post(
        "/api/v1/quotations",
        json={
            "customer_name": "ABC Manufacturing",
            "product_id": product_id,
            "quantity": 10,
            "requirements": [req.model_dump(mode="json") for req in DEMO_REQUIREMENTS],
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "QUOTATION_VALIDATION_UNKNOWN"


@pytest.mark.asyncio
async def test_quotation_api_validation_failure(seeded_client):
    products = await seeded_client.get("/api/v1/products", params={"model_number": "VIS-SW-003"})
    product_id = products.json()["items"][0]["id"]

    response = await seeded_client.post(
        "/api/v1/quotations",
        json={
            "customer_name": "ABC Manufacturing",
            "product_id": product_id,
            "quantity": 10,
            "requirements": [req.model_dump(mode="json") for req in DEMO_REQUIREMENTS],
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "QUOTATION_VALIDATION_FAILED"


@pytest.mark.asyncio
async def test_quotation_api_approve(seeded_client):
    products = await seeded_client.get("/api/v1/products", params={"model_number": "NS-SW-005"})
    product_id = products.json()["items"][0]["id"]
    create_response = await seeded_client.post(
        "/api/v1/quotations",
        json={
            "customer_name": "ABC Manufacturing",
            "product_id": product_id,
            "quantity": 10,
            "requirements": [req.model_dump(mode="json") for req in DEMO_REQUIREMENTS],
        },
    )
    quotation_id = create_response.json()["id"]

    approve_response = await seeded_client.patch(
        f"/api/v1/quotations/{quotation_id}/status",
        json={"status": "APPROVED"},
    )
    assert approve_response.status_code == 200
    assert approve_response.json()["status"] == "APPROVED"
