"""Idempotent synthetic product catalog seed for Phase 2."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.domain.spec_keys import SpecKey
from app.models.manufacturer import Manufacturer
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.product_pricing import ProductPricing
from app.models.product_specification import ProductSpecification
from app.seed.db_checks import (
    CATALOG_REQUIRED_TABLES,
    verify_required_tables,
    wrap_seed_database_errors,
)


@dataclass(frozen=True)
class SpecSeed:
    spec_key: SpecKey
    numeric_value: Decimal | None = None
    text_value: str | None = None
    boolean_value: bool | None = None
    unit: str | None = None
    source: str | None = "synthetic_seed"


@dataclass(frozen=True)
class PricingSeed:
    unit_price: Decimal
    currency: str = "USD"
    discount_percent: Decimal = Decimal("0")
    lead_time_days: int = 14
    price_valid_until: date | None = None


@dataclass(frozen=True)
class ProductSeed:
    model_number: str
    name: str
    manufacturer_name: str
    category_slug: str
    description: str
    specifications: tuple[SpecSeed, ...] = field(default_factory=tuple)
    pricing: PricingSeed | None = None


MANUFACTURERS: tuple[dict[str, Any], ...] = (
    {
        "name": "Northstar Automation",
        "description": "Fictional automation components manufacturer for MVP demos.",
        "website": "https://example.invalid/northstar-automation",
    },
    {
        "name": "Vector Industrial Systems",
        "description": "Fictional industrial systems supplier for MVP demos.",
        "website": "https://example.invalid/vector-industrial",
    },
    {
        "name": "Apex Controls",
        "description": "Fictional controls vendor for MVP demos.",
        "website": "https://example.invalid/apex-controls",
    },
)

CATEGORIES: tuple[dict[str, str], ...] = (
    {
        "name": "PLC",
        "slug": "plc",
        "description": "Programmable logic controllers for industrial automation.",
    },
    {
        "name": "HMI",
        "slug": "hmi",
        "description": "Human-machine interfaces for operator visualization.",
    },
    {
        "name": "Power Supply",
        "slug": "power-supply",
        "description": "Industrial DC power supplies for control panels.",
    },
    {
        "name": "Industrial Ethernet Switch",
        "slug": "industrial-ethernet-switch",
        "description": "Managed and unmanaged industrial Ethernet switches.",
    },
)

PRODUCTS: tuple[ProductSeed, ...] = (
    ProductSeed(
        model_number="NS-SW-005",
        name="Industrial Ethernet Switch 5-Port",
        manufacturer_name="Northstar Automation",
        category_slug="industrial-ethernet-switch",
        description="Five-port managed industrial Ethernet switch for control panels.",
        specifications=(
            SpecSeed(SpecKey.INPUT_VOLTAGE, numeric_value=Decimal("24"), unit="V"),
            SpecSeed(SpecKey.ETHERNET_PORTS, numeric_value=Decimal("5")),
            SpecSeed(SpecKey.DIN_RAIL_MOUNTABLE, boolean_value=True),
            SpecSeed(SpecKey.SUPPORTS_MODBUS_TCP, boolean_value=True),
            SpecSeed(SpecKey.OPERATING_TEMP_MIN, numeric_value=Decimal("-20"), unit="°C"),
        ),
        pricing=PricingSeed(
            unit_price=Decimal("185.00"),
            discount_percent=Decimal("5"),
            lead_time_days=14,
        ),
    ),
    ProductSeed(
        model_number="VIS-SW-003",
        name="Industrial Ethernet Switch 3-Port",
        manufacturer_name="Vector Industrial Systems",
        category_slug="industrial-ethernet-switch",
        description="Compact three-port industrial Ethernet switch.",
        specifications=(
            SpecSeed(SpecKey.INPUT_VOLTAGE, numeric_value=Decimal("24"), unit="V"),
            SpecSeed(SpecKey.ETHERNET_PORTS, numeric_value=Decimal("3")),
            SpecSeed(SpecKey.DIN_RAIL_MOUNTABLE, boolean_value=True),
            SpecSeed(SpecKey.SUPPORTS_MODBUS_TCP, boolean_value=True),
            SpecSeed(SpecKey.OPERATING_TEMP_MIN, numeric_value=Decimal("-20"), unit="°C"),
        ),
        pricing=PricingSeed(
            unit_price=Decimal("145.00"),
            discount_percent=Decimal("3"),
            lead_time_days=10,
        ),
    ),
    ProductSeed(
        model_number="AC-SW-008",
        name="Industrial Ethernet Switch 8-Port",
        manufacturer_name="Apex Controls",
        category_slug="industrial-ethernet-switch",
        description="Eight-port industrial Ethernet switch without published minimum temperature.",
        specifications=(
            SpecSeed(SpecKey.INPUT_VOLTAGE, numeric_value=Decimal("24"), unit="V"),
            SpecSeed(SpecKey.ETHERNET_PORTS, numeric_value=Decimal("8")),
            SpecSeed(SpecKey.DIN_RAIL_MOUNTABLE, boolean_value=True),
            SpecSeed(SpecKey.SUPPORTS_MODBUS_TCP, boolean_value=True),
        ),
        pricing=PricingSeed(
            unit_price=Decimal("210.00"),
            discount_percent=Decimal("0"),
            lead_time_days=21,
        ),
    ),
    ProductSeed(
        model_number="NS-SW-012",
        name="Industrial Ethernet Switch 12-Port",
        manufacturer_name="Northstar Automation",
        category_slug="industrial-ethernet-switch",
        description="Twelve-port managed switch for larger panel networks.",
        specifications=(
            SpecSeed(SpecKey.INPUT_VOLTAGE, numeric_value=Decimal("24"), unit="V"),
            SpecSeed(SpecKey.ETHERNET_PORTS, numeric_value=Decimal("12")),
            SpecSeed(SpecKey.DIN_RAIL_MOUNTABLE, boolean_value=True),
            SpecSeed(SpecKey.SUPPORTS_MODBUS_TCP, boolean_value=True),
            SpecSeed(SpecKey.OPERATING_TEMP_MIN, numeric_value=Decimal("-10"), unit="°C"),
        ),
        pricing=PricingSeed(unit_price=Decimal("265.00"), lead_time_days=18),
    ),
    ProductSeed(
        model_number="NS-PLC-101",
        name="Compact PLC 16 I/O",
        manufacturer_name="Northstar Automation",
        category_slug="plc",
        description="Compact PLC with 16 digital I/O points.",
        specifications=(
            SpecSeed(SpecKey.INPUT_VOLTAGE, numeric_value=Decimal("24"), unit="V"),
            SpecSeed(SpecKey.DIN_RAIL_MOUNTABLE, boolean_value=True),
            SpecSeed(SpecKey.SUPPORTS_MODBUS_TCP, boolean_value=True),
            SpecSeed(SpecKey.IP_RATING, text_value="IP20"),
        ),
        pricing=PricingSeed(unit_price=Decimal("420.00"), lead_time_days=12),
    ),
    ProductSeed(
        model_number="VIS-PLC-201",
        name="Modular PLC CPU",
        manufacturer_name="Vector Industrial Systems",
        category_slug="plc",
        description="Modular PLC CPU for distributed I/O racks.",
        specifications=(
            SpecSeed(SpecKey.INPUT_VOLTAGE, numeric_value=Decimal("24"), unit="V"),
            SpecSeed(SpecKey.DIN_RAIL_MOUNTABLE, boolean_value=True),
            SpecSeed(SpecKey.SUPPORTS_MODBUS_TCP, boolean_value=True),
            SpecSeed(SpecKey.IP_RATING, text_value="IP20"),
        ),
        pricing=PricingSeed(
            unit_price=Decimal("510.00"),
            discount_percent=Decimal("2"),
            lead_time_days=15,
        ),
    ),
    ProductSeed(
        model_number="AC-PLC-301",
        name="Safety PLC 8 I/O",
        manufacturer_name="Apex Controls",
        category_slug="plc",
        description="Safety-rated PLC for machine guarding applications.",
        specifications=(
            SpecSeed(SpecKey.INPUT_VOLTAGE, numeric_value=Decimal("24"), unit="V"),
            SpecSeed(SpecKey.DIN_RAIL_MOUNTABLE, boolean_value=True),
            SpecSeed(SpecKey.SUPPORTS_MODBUS_TCP, boolean_value=False),
            SpecSeed(SpecKey.IP_RATING, text_value="IP20"),
        ),
        pricing=PricingSeed(unit_price=Decimal("890.00"), lead_time_days=20),
    ),
    ProductSeed(
        model_number="NS-PLC-102",
        name="Performance PLC 32 I/O",
        manufacturer_name="Northstar Automation",
        category_slug="plc",
        description="Higher-capacity PLC for multi-axis coordination.",
        specifications=(
            SpecSeed(SpecKey.INPUT_VOLTAGE, numeric_value=Decimal("24"), unit="V"),
            SpecSeed(SpecKey.DIN_RAIL_MOUNTABLE, boolean_value=True),
            SpecSeed(SpecKey.SUPPORTS_MODBUS_TCP, boolean_value=True),
            SpecSeed(SpecKey.OPERATING_TEMP_MIN, numeric_value=Decimal("0"), unit="°C"),
            SpecSeed(SpecKey.OPERATING_TEMP_MAX, numeric_value=Decimal("55"), unit="°C"),
        ),
        pricing=PricingSeed(unit_price=Decimal("675.00"), lead_time_days=14),
    ),
    ProductSeed(
        model_number="NS-HMI-401",
        name="7-inch Panel HMI",
        manufacturer_name="Northstar Automation",
        category_slug="hmi",
        description="Seven-inch resistive touch panel HMI.",
        specifications=(
            SpecSeed(SpecKey.INPUT_VOLTAGE, numeric_value=Decimal("24"), unit="V"),
            SpecSeed(SpecKey.DIN_RAIL_MOUNTABLE, boolean_value=False),
            SpecSeed(SpecKey.MOUNTING, text_value="panel_mount"),
            SpecSeed(SpecKey.IP_RATING, text_value="IP65"),
        ),
        pricing=PricingSeed(unit_price=Decimal("395.00"), lead_time_days=10),
    ),
    ProductSeed(
        model_number="VIS-HMI-501",
        name="10-inch Wide HMI",
        manufacturer_name="Vector Industrial Systems",
        category_slug="hmi",
        description="Ten-inch widescreen operator panel.",
        specifications=(
            SpecSeed(SpecKey.INPUT_VOLTAGE, numeric_value=Decimal("24"), unit="V"),
            SpecSeed(SpecKey.MOUNTING, text_value="panel_mount"),
            SpecSeed(SpecKey.IP_RATING, text_value="IP65"),
            SpecSeed(SpecKey.SUPPORTS_MODBUS_TCP, boolean_value=True),
        ),
        pricing=PricingSeed(
            unit_price=Decimal("520.00"),
            discount_percent=Decimal("4"),
            lead_time_days=16,
        ),
    ),
    ProductSeed(
        model_number="AC-HMI-601",
        name="4-inch Compact HMI",
        manufacturer_name="Apex Controls",
        category_slug="hmi",
        description="Compact four-inch HMI for space-constrained panels.",
        specifications=(
            SpecSeed(SpecKey.INPUT_VOLTAGE, numeric_value=Decimal("24"), unit="V"),
            SpecSeed(SpecKey.MOUNTING, text_value="panel_mount"),
            SpecSeed(SpecKey.IP_RATING, text_value="IP54"),
        ),
        pricing=PricingSeed(unit_price=Decimal("285.00"), lead_time_days=9),
    ),
    ProductSeed(
        model_number="NS-PSU-701",
        name="24 VDC Power Supply 5 A",
        manufacturer_name="Northstar Automation",
        category_slug="power-supply",
        description="Single-phase 24 VDC DIN-rail power supply.",
        specifications=(
            SpecSeed(SpecKey.INPUT_VOLTAGE, numeric_value=Decimal("100"), unit="V"),
            SpecSeed(SpecKey.OUTPUT_VOLTAGE, numeric_value=Decimal("24"), unit="V"),
            SpecSeed(SpecKey.OUTPUT_CURRENT_MAX, numeric_value=Decimal("5"), unit="A"),
            SpecSeed(SpecKey.DIN_RAIL_MOUNTABLE, boolean_value=True),
        ),
        pricing=PricingSeed(unit_price=Decimal("95.00"), lead_time_days=7),
    ),
    ProductSeed(
        model_number="VIS-PSU-801",
        name="24 VDC Power Supply 10 A",
        manufacturer_name="Vector Industrial Systems",
        category_slug="power-supply",
        description="Ten-amp industrial power supply for larger loads.",
        specifications=(
            SpecSeed(SpecKey.INPUT_VOLTAGE, numeric_value=Decimal("240"), unit="V"),
            SpecSeed(SpecKey.OUTPUT_VOLTAGE, numeric_value=Decimal("24"), unit="V"),
            SpecSeed(SpecKey.OUTPUT_CURRENT_MAX, numeric_value=Decimal("10"), unit="A"),
            SpecSeed(SpecKey.DIN_RAIL_MOUNTABLE, boolean_value=True),
        ),
        pricing=PricingSeed(
            unit_price=Decimal("135.00"),
            discount_percent=Decimal("5"),
            lead_time_days=8,
        ),
    ),
    ProductSeed(
        model_number="AC-PSU-901",
        name="24 VDC Power Supply 2.5 A",
        manufacturer_name="Apex Controls",
        category_slug="power-supply",
        description="Economy 2.5 A power supply for small control circuits.",
        specifications=(
            SpecSeed(SpecKey.INPUT_VOLTAGE, numeric_value=Decimal("120"), unit="V"),
            SpecSeed(SpecKey.OUTPUT_VOLTAGE, numeric_value=Decimal("24"), unit="V"),
            SpecSeed(SpecKey.OUTPUT_CURRENT_MAX, numeric_value=Decimal("2.5"), unit="A"),
            SpecSeed(SpecKey.DIN_RAIL_MOUNTABLE, boolean_value=True),
        ),
        pricing=PricingSeed(unit_price=Decimal("68.00"), lead_time_days=6),
    ),
    ProductSeed(
        model_number="NS-PSU-702",
        name="24 VDC Power Supply 20 A",
        manufacturer_name="Northstar Automation",
        category_slug="power-supply",
        description="High-current power supply for multi-device panels.",
        specifications=(
            SpecSeed(SpecKey.INPUT_VOLTAGE, numeric_value=Decimal("240"), unit="V"),
            SpecSeed(SpecKey.OUTPUT_VOLTAGE, numeric_value=Decimal("24"), unit="V"),
            SpecSeed(SpecKey.OUTPUT_CURRENT_MAX, numeric_value=Decimal("20"), unit="A"),
            SpecSeed(SpecKey.DIN_RAIL_MOUNTABLE, boolean_value=True),
        ),
        pricing=PricingSeed(unit_price=Decimal("210.00"), lead_time_days=11),
    ),
    ProductSeed(
        model_number="AC-SW-015",
        name="Industrial Ethernet Switch 16-Port",
        manufacturer_name="Apex Controls",
        category_slug="industrial-ethernet-switch",
        description="Sixteen-port switch for plant-floor aggregation.",
        specifications=(
            SpecSeed(SpecKey.INPUT_VOLTAGE, numeric_value=Decimal("24"), unit="V"),
            SpecSeed(SpecKey.ETHERNET_PORTS, numeric_value=Decimal("16")),
            SpecSeed(SpecKey.DIN_RAIL_MOUNTABLE, boolean_value=True),
            SpecSeed(SpecKey.SUPPORTS_MODBUS_TCP, boolean_value=True),
            SpecSeed(SpecKey.OPERATING_TEMP_MIN, numeric_value=Decimal("-25"), unit="°C"),
        ),
        pricing=PricingSeed(unit_price=Decimal("325.00"), lead_time_days=19),
    ),
)


async def _get_or_create_manufacturer(session: AsyncSession, data: dict[str, Any]) -> Manufacturer:
    manufacturer = await session.scalar(
        select(Manufacturer).where(Manufacturer.name == data["name"]),
    )
    if manufacturer is None:
        manufacturer = Manufacturer(**data)
        session.add(manufacturer)
        await session.flush()
    return manufacturer


async def _get_or_create_category(session: AsyncSession, data: dict[str, str]) -> ProductCategory:
    category = await session.scalar(
        select(ProductCategory).where(ProductCategory.slug == data["slug"]),
    )
    if category is None:
        category = ProductCategory(**data)
        session.add(category)
        await session.flush()
    return category


async def _get_or_create_product(
    session: AsyncSession,
    seed: ProductSeed,
    manufacturer: Manufacturer,
    category: ProductCategory,
) -> Product:
    product = await session.scalar(
        select(Product).where(Product.model_number == seed.model_number),
    )
    if product is None:
        product = Product(
            manufacturer_id=manufacturer.id,
            category_id=category.id,
            model_number=seed.model_number,
            name=seed.name,
            description=seed.description,
        )
        session.add(product)
        await session.flush()
    return product


async def _upsert_specification(
    session: AsyncSession,
    product: Product,
    spec: SpecSeed,
) -> None:
    existing = await session.scalar(
        select(ProductSpecification).where(
            ProductSpecification.product_id == product.id,
            ProductSpecification.spec_key == spec.spec_key.value,
        ),
    )
    if existing is None:
        existing = ProductSpecification(
            product_id=product.id,
            spec_key=spec.spec_key.value,
        )
        session.add(existing)

    existing.numeric_value = spec.numeric_value
    existing.text_value = spec.text_value
    existing.boolean_value = spec.boolean_value
    existing.unit = spec.unit
    existing.source = spec.source


async def _upsert_pricing(
    session: AsyncSession,
    product: Product,
    pricing: PricingSeed,
) -> None:
    existing = await session.scalar(
        select(ProductPricing).where(ProductPricing.product_id == product.id),
    )
    if existing is None:
        existing = ProductPricing(product_id=product.id)
        session.add(existing)

    existing.unit_price = pricing.unit_price
    existing.currency = pricing.currency
    existing.discount_percent = pricing.discount_percent
    existing.lead_time_days = pricing.lead_time_days
    existing.price_valid_until = pricing.price_valid_until


@wrap_seed_database_errors
async def seed_catalog(session: AsyncSession) -> None:
    await verify_required_tables(session, CATALOG_REQUIRED_TABLES)

    manufacturers_by_name: dict[str, Manufacturer] = {}
    for data in MANUFACTURERS:
        manufacturers_by_name[data["name"]] = await _get_or_create_manufacturer(session, data)

    categories_by_slug: dict[str, ProductCategory] = {}
    for data in CATEGORIES:
        categories_by_slug[data["slug"]] = await _get_or_create_category(session, data)

    for product_seed in PRODUCTS:
        manufacturer = manufacturers_by_name[product_seed.manufacturer_name]
        category = categories_by_slug[product_seed.category_slug]
        product = await _get_or_create_product(session, product_seed, manufacturer, category)

        for spec in product_seed.specifications:
            await _upsert_specification(session, product, spec)

        if product_seed.pricing is not None:
            await _upsert_pricing(session, product, product_seed.pricing)

    await session.commit()


async def run_seed() -> None:
    settings = get_settings()
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    try:
        async with session_factory() as session:
            await seed_catalog(session)
    except RuntimeError as exc:
        print(str(exc), file=__import__("sys").stderr)
        raise SystemExit(1) from exc
    finally:
        await engine.dispose()


def main() -> None:
    asyncio.run(run_seed())


if __name__ == "__main__":
    main()
