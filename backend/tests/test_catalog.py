from decimal import Decimal

import pytest
from sqlalchemy import func, select

from app.domain.spec_keys import SpecKey
from app.models.manufacturer import Manufacturer
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.product_pricing import ProductPricing
from app.models.product_specification import ProductSpecification
from app.seed.catalog import CATEGORIES, MANUFACTURERS, PRODUCTS, seed_catalog


@pytest.mark.asyncio
async def test_seed_is_idempotent(db_session):
    await seed_catalog(db_session)
    manufacturer_count = await db_session.scalar(select(func.count()).select_from(Manufacturer))
    category_count = await db_session.scalar(select(func.count()).select_from(ProductCategory))
    product_count = await db_session.scalar(select(func.count()).select_from(Product))

    await seed_catalog(db_session)

    mfg_count_after = await db_session.scalar(select(func.count()).select_from(Manufacturer))
    cat_count_after = await db_session.scalar(select(func.count()).select_from(ProductCategory))
    product_count_after = await db_session.scalar(select(func.count()).select_from(Product))
    assert mfg_count_after == manufacturer_count
    assert cat_count_after == category_count
    assert product_count_after == product_count
    assert manufacturer_count == len(MANUFACTURERS)
    assert category_count == len(CATEGORIES)
    assert product_count == len(PRODUCTS)


@pytest.mark.asyncio
async def test_manufacturer_uniqueness(db_session):
    await seed_catalog(db_session)
    names = (await db_session.scalars(select(Manufacturer.name))).all()
    assert len(names) == len(set(names))


@pytest.mark.asyncio
async def test_category_unique_slug(db_session):
    await seed_catalog(db_session)
    slugs = (await db_session.scalars(select(ProductCategory.slug))).all()
    assert len(slugs) == len(set(slugs))
    assert "industrial-ethernet-switch" in slugs


@pytest.mark.asyncio
async def test_demo_switch_specifications(db_session):
    await seed_catalog(db_session)

    async def spec_map(model_number: str) -> dict[str, ProductSpecification]:
        product = await db_session.scalar(
            select(Product).where(Product.model_number == model_number),
        )
        assert product is not None
        specs = (
            await db_session.scalars(
                select(ProductSpecification).where(ProductSpecification.product_id == product.id),
            )
        ).all()
        return {spec.spec_key: spec for spec in specs}

    pass_specs = await spec_map("NS-SW-005")
    assert pass_specs[SpecKey.INPUT_VOLTAGE.value].numeric_value == Decimal("24")
    assert pass_specs[SpecKey.INPUT_VOLTAGE.value].unit == "V"
    assert pass_specs[SpecKey.ETHERNET_PORTS.value].numeric_value == Decimal("5")
    assert pass_specs[SpecKey.DIN_RAIL_MOUNTABLE.value].boolean_value is True
    assert pass_specs[SpecKey.SUPPORTS_MODBUS_TCP.value].boolean_value is True
    assert pass_specs[SpecKey.OPERATING_TEMP_MIN.value].numeric_value == Decimal("-20")

    fail_specs = await spec_map("VIS-SW-003")
    assert fail_specs[SpecKey.ETHERNET_PORTS.value].numeric_value == Decimal("3")

    unknown_specs = await spec_map("AC-SW-008")
    assert SpecKey.OPERATING_TEMP_MIN.value not in unknown_specs


@pytest.mark.asyncio
async def test_demo_switch_pricing(db_session):
    await seed_catalog(db_session)

    async def pricing_for(model_number: str) -> ProductPricing:
        product = await db_session.scalar(
            select(Product).where(Product.model_number == model_number),
        )
        assert product is not None
        pricing = await db_session.scalar(
            select(ProductPricing).where(ProductPricing.product_id == product.id),
        )
        assert pricing is not None
        return pricing

    pass_pricing = await pricing_for("NS-SW-005")
    assert pass_pricing.unit_price == Decimal("185.00")
    assert pass_pricing.currency == "USD"
    assert pass_pricing.discount_percent == Decimal("5")
    assert pass_pricing.lead_time_days == 14


@pytest.mark.asyncio
async def test_list_manufacturers(seeded_client):
    response = await seeded_client.get("/api/v1/manufacturers")
    assert response.status_code == 200
    payload = response.json()
    names = {item["name"] for item in payload["items"]}
    assert names == {
        "Northstar Automation",
        "Vector Industrial Systems",
        "Apex Controls",
    }


@pytest.mark.asyncio
async def test_list_product_categories(seeded_client):
    response = await seeded_client.get("/api/v1/product-categories")
    assert response.status_code == 200
    payload = response.json()
    slugs = {item["slug"] for item in payload["items"]}
    assert slugs == {"plc", "hmi", "power-supply", "industrial-ethernet-switch"}


@pytest.mark.asyncio
async def test_list_products_and_filtering(seeded_client):
    response = await seeded_client.get("/api/v1/products")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == len(PRODUCTS)
    assert len(payload["items"]) == len(PRODUCTS)

    category_response = await seeded_client.get(
        "/api/v1/products",
        params={"category": "industrial-ethernet-switch"},
    )
    assert category_response.status_code == 200
    category_items = category_response.json()["items"]
    assert len(category_items) == 5
    assert all(item["category"]["slug"] == "industrial-ethernet-switch" for item in category_items)

    manufacturer_response = await seeded_client.get(
        "/api/v1/products",
        params={"manufacturer": "Northstar Automation"},
    )
    assert manufacturer_response.status_code == 200
    manufacturer_items = manufacturer_response.json()["items"]
    assert len(manufacturer_items) >= 1
    assert all(
        item["manufacturer"]["name"] == "Northstar Automation" for item in manufacturer_items
    )

    model_response = await seeded_client.get(
        "/api/v1/products",
        params={"model_number": "NS-SW-005"},
    )
    assert model_response.status_code == 200
    model_items = model_response.json()["items"]
    assert len(model_items) == 1
    assert model_items[0]["model_number"] == "NS-SW-005"


@pytest.mark.asyncio
async def test_get_product_detail(seeded_client):
    list_response = await seeded_client.get(
        "/api/v1/products",
        params={"model_number": "NS-SW-005"},
    )
    product_id = list_response.json()["items"][0]["id"]

    response = await seeded_client.get(f"/api/v1/products/{product_id}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["model_number"] == "NS-SW-005"
    assert payload["manufacturer"]["name"] == "Northstar Automation"
    assert payload["category"]["name"] == "Industrial Ethernet Switch"
    assert payload["pricing"]["unit_price"] == "185.00"
    spec_keys = {spec["spec_key"] for spec in payload["specifications"]}
    assert SpecKey.ETHERNET_PORTS.value in spec_keys


@pytest.mark.asyncio
async def test_get_product_not_found(seeded_client):
    response = await seeded_client.get(
        "/api/v1/products/00000000-0000-0000-0000-000000000001",
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
