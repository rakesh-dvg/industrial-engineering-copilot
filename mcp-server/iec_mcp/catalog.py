"""In-memory demo catalog — no database or network access."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass(frozen=True, slots=True)
class ProductRecord:
    model_number: str
    name: str
    manufacturer: str
    category: str
    unit_price: Decimal
    currency: str
    lead_time_days: int
    specifications: dict[str, Any]


DEMO_PRODUCTS: tuple[ProductRecord, ...] = (
    ProductRecord(
        model_number="NS-SW-005",
        name="Northstar Industrial Ethernet Switch",
        manufacturer="Northstar Automation",
        category="ethernet-switch",
        unit_price=Decimal("185.00"),
        currency="USD",
        lead_time_days=14,
        specifications={
            "supply_voltage_v": 24,
            "port_count": 8,
            "mounting": "DIN rail",
            "protocols": ["Modbus TCP"],
            "operating_temp_min_c": -20,
        },
    ),
    ProductRecord(
        model_number="VIS-SW-003",
        name="Vector Lite Ethernet Switch",
        manufacturer="Vector Industrial Systems",
        category="ethernet-switch",
        unit_price=Decimal("142.00"),
        currency="USD",
        lead_time_days=21,
        specifications={
            "supply_voltage_v": 12,
            "port_count": 5,
            "mounting": "panel",
            "protocols": ["Modbus TCP"],
            "operating_temp_min_c": 0,
        },
    ),
    ProductRecord(
        model_number="AC-SW-008",
        name="Apex Compact Switch",
        manufacturer="Apex Controls",
        category="ethernet-switch",
        unit_price=Decimal("165.00"),
        currency="USD",
        lead_time_days=10,
        specifications={
            "supply_voltage_v": 24,
            "port_count": 4,
            "mounting": "DIN rail",
            "protocols": [],
            "operating_temp_min_c": None,
        },
    ),
)


def search_products(query: str) -> list[dict[str, Any]]:
    needle = query.strip().lower()
    results: list[dict[str, Any]] = []
    for product in DEMO_PRODUCTS:
        haystack = " ".join(
            [
                product.model_number,
                product.name,
                product.manufacturer,
                product.category,
            ]
        ).lower()
        if not needle or needle in haystack:
            results.append(_product_summary(product))
    return results


def get_product(model_number: str) -> dict[str, Any] | None:
    for product in DEMO_PRODUCTS:
        if product.model_number.lower() == model_number.strip().lower():
            return {
                **_product_summary(product),
                "specifications": product.specifications,
            }
    return None


def validate_requirement(model_number: str, spec_key: str, operator: str, value: str) -> dict[str, str]:
    product = get_product(model_number)
    if product is None:
        return {"status": "UNKNOWN", "reason": "Product not in demo catalog."}

    specs = product["specifications"]
    key = spec_key.strip().lower()
    if key == "supply_voltage_v" and operator in (">=", "gte"):
        actual = specs.get("supply_voltage_v")
        if actual is None:
            return {"status": "UNKNOWN", "reason": "Voltage not documented."}
        try:
            required = float(value)
        except ValueError:
            return {"status": "UNKNOWN", "reason": "Invalid requirement value."}
        return {
            "status": "PASS" if float(actual) >= required else "FAIL",
            "reason": f"Catalog voltage {actual} V vs required {required} V.",
        }
    if key == "port_count" and operator in (">=", "gte"):
        actual = specs.get("port_count")
        if actual is None:
            return {"status": "UNKNOWN", "reason": "Port count not documented."}
        try:
            required = int(value)
        except ValueError:
            return {"status": "UNKNOWN", "reason": "Invalid requirement value."}
        return {
            "status": "PASS" if int(actual) >= required else "FAIL",
            "reason": f"Catalog ports {actual} vs required {required}.",
        }
    return {"status": "UNKNOWN", "reason": f"Demo validator does not handle {spec_key}."}


def create_quote_draft(model_number: str, quantity: int) -> dict[str, Any]:
    product = get_product(model_number)
    if product is None:
        raise ValueError("Unknown product model.")
    if quantity <= 0:
        raise ValueError("Quantity must be positive.")
    unit = Decimal(str(product["unit_price"]))
    total = unit * quantity
    return {
        "model_number": product["model_number"],
        "quantity": quantity,
        "unit_price": str(unit),
        "currency": product["currency"],
        "total": str(total),
        "status": "DRAFT",
        "requires_human_approval": True,
        "note": "Draft only — create official quotation via FastAPI after sales approval.",
    }


def _product_summary(product: ProductRecord) -> dict[str, Any]:
    return {
        "model_number": product.model_number,
        "name": product.name,
        "manufacturer": product.manufacturer,
        "category": product.category,
        "unit_price": str(product.unit_price),
        "currency": product.currency,
        "lead_time_days": product.lead_time_days,
    }
