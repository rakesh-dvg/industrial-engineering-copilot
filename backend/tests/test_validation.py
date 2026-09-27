"""Phase 4 deterministic validation tests."""

from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.domain.spec_keys import SpecKey
from app.models.product import Product
from app.models.product_specification import ProductSpecification
from app.schemas.rfq import RequirementOperator, RequirementPriority, StructuredRequirement
from app.schemas.validation import ValidationStatus
from app.seed.catalog import seed_catalog
from app.services.validation import (
    compute_overall_status,
    evaluate_requirement,
    validate_product,
)


def _spec(
    spec_key: SpecKey,
    *,
    numeric: Decimal | None = None,
    unit: str | None = None,
    boolean: bool | None = None,
    text: str | None = None,
) -> ProductSpecification:
    return ProductSpecification(
        id=uuid4(),
        product_id=uuid4(),
        spec_key=spec_key.value,
        numeric_value=numeric,
        unit=unit,
        boolean_value=boolean,
        text_value=text,
    )


def _req(
    spec_key: SpecKey,
    operator: RequirementOperator,
    value,
    *,
    unit: str | None = None,
    required: bool = True,
    priority: RequirementPriority | None = None,
) -> StructuredRequirement:
    return StructuredRequirement(
        spec_key=spec_key,
        operator=operator,
        value=value,
        unit=unit,
        required=required,
        priority=priority,
    )


@pytest.mark.parametrize(
    ("actual", "required_value", "expected"),
    [
        (Decimal("24"), 24, ValidationStatus.PASS),
        (Decimal("12"), 24, ValidationStatus.FAIL),
        (None, 24, ValidationStatus.UNKNOWN),
    ],
)
def test_eq_voltage(actual, required_value, expected):
    spec = _spec(SpecKey.INPUT_VOLTAGE, numeric=actual, unit="V") if actual else None
    requirement = _req(SpecKey.INPUT_VOLTAGE, RequirementOperator.EQ, required_value, unit="V")
    assert evaluate_requirement(requirement, spec).status == expected


@pytest.mark.parametrize(
    ("actual", "expected"),
    [
        (Decimal("8"), ValidationStatus.PASS),
        (Decimal("5"), ValidationStatus.FAIL),
        (Decimal("3"), ValidationStatus.FAIL),
        (None, ValidationStatus.UNKNOWN),
    ],
)
def test_gt_ethernet_ports(actual, expected):
    spec = _spec(SpecKey.ETHERNET_PORTS, numeric=actual) if actual else None
    requirement = _req(SpecKey.ETHERNET_PORTS, RequirementOperator.GT, 5)
    assert evaluate_requirement(requirement, spec).status == expected


@pytest.mark.parametrize(
    ("actual", "expected"),
    [
        (Decimal("8"), ValidationStatus.PASS),
        (Decimal("5"), ValidationStatus.PASS),
        (Decimal("3"), ValidationStatus.FAIL),
        (None, ValidationStatus.UNKNOWN),
    ],
)
def test_gte_ethernet_ports(actual, expected):
    spec = _spec(SpecKey.ETHERNET_PORTS, numeric=actual) if actual else None
    requirement = _req(SpecKey.ETHERNET_PORTS, RequirementOperator.GTE, 5)
    assert evaluate_requirement(requirement, spec).status == expected


@pytest.mark.parametrize(
    ("actual", "expected"),
    [
        (Decimal("3"), ValidationStatus.PASS),
        (Decimal("5"), ValidationStatus.FAIL),
        (Decimal("8"), ValidationStatus.FAIL),
        (None, ValidationStatus.UNKNOWN),
    ],
)
def test_lt_ethernet_ports(actual, expected):
    spec = _spec(SpecKey.ETHERNET_PORTS, numeric=actual) if actual else None
    requirement = _req(SpecKey.ETHERNET_PORTS, RequirementOperator.LT, 5)
    assert evaluate_requirement(requirement, spec).status == expected


@pytest.mark.parametrize(
    ("actual", "expected"),
    [
        (Decimal("3"), ValidationStatus.PASS),
        (Decimal("5"), ValidationStatus.PASS),
        (Decimal("8"), ValidationStatus.FAIL),
        (None, ValidationStatus.UNKNOWN),
    ],
)
def test_lte_ethernet_ports(actual, expected):
    spec = _spec(SpecKey.ETHERNET_PORTS, numeric=actual) if actual else None
    requirement = _req(SpecKey.ETHERNET_PORTS, RequirementOperator.LTE, 5)
    assert evaluate_requirement(requirement, spec).status == expected


def test_neq_voltage():
    requirement = _req(SpecKey.INPUT_VOLTAGE, RequirementOperator.NEQ, 24, unit="V")

    pass_spec = _spec(SpecKey.INPUT_VOLTAGE, numeric=Decimal("12"), unit="V")
    assert evaluate_requirement(requirement, pass_spec).status == ValidationStatus.PASS

    fail_spec = _spec(SpecKey.INPUT_VOLTAGE, numeric=Decimal("24"), unit="V")
    assert evaluate_requirement(requirement, fail_spec).status == ValidationStatus.FAIL

    assert evaluate_requirement(requirement, None).status == ValidationStatus.UNKNOWN


def test_boolean_eq():
    spec = _spec(SpecKey.DIN_RAIL_MOUNTABLE, boolean=True)
    requirement = _req(SpecKey.DIN_RAIL_MOUNTABLE, RequirementOperator.EQ, True)
    assert evaluate_requirement(requirement, spec).status == ValidationStatus.PASS

    spec_false = _spec(SpecKey.DIN_RAIL_MOUNTABLE, boolean=False)
    assert evaluate_requirement(requirement, spec_false).status == ValidationStatus.FAIL

    assert evaluate_requirement(requirement, None).status == ValidationStatus.UNKNOWN


def test_contains_text():
    spec = _spec(SpecKey.MOUNTING, text="DIN rail / wall mount")
    requirement = _req(SpecKey.MOUNTING, RequirementOperator.CONTAINS, "DIN rail")
    assert evaluate_requirement(requirement, spec).status == ValidationStatus.PASS

    spec_fail = _spec(SpecKey.MOUNTING, text="wall")
    assert evaluate_requirement(requirement, spec_fail).status == ValidationStatus.FAIL
    assert evaluate_requirement(requirement, None).status == ValidationStatus.UNKNOWN


def test_in_text():
    spec = _spec(SpecKey.MOUNTING, text="DIN rail")
    requirement = _req(
        SpecKey.MOUNTING,
        RequirementOperator.IN,
        ["DIN rail", "panel"],
    )
    assert evaluate_requirement(requirement, spec).status == ValidationStatus.PASS

    spec_fail = _spec(SpecKey.MOUNTING, text="wall")
    assert evaluate_requirement(requirement, spec_fail).status == ValidationStatus.FAIL
    assert evaluate_requirement(requirement, None).status == ValidationStatus.UNKNOWN


def test_unit_normalization_voltage():
    spec = _spec(SpecKey.INPUT_VOLTAGE, numeric=Decimal("24"), unit="V")
    requirement = _req(SpecKey.INPUT_VOLTAGE, RequirementOperator.EQ, 24000, unit="mV")
    assert evaluate_requirement(requirement, spec).status == ValidationStatus.PASS

    spec_kv = _spec(SpecKey.INPUT_VOLTAGE, numeric=Decimal("0.024"), unit="kV")
    requirement_v = _req(SpecKey.INPUT_VOLTAGE, RequirementOperator.EQ, 24, unit="V")
    assert evaluate_requirement(requirement_v, spec_kv).status == ValidationStatus.PASS


def test_unit_normalization_current():
    spec = _spec(SpecKey.OUTPUT_CURRENT_MAX, numeric=Decimal("0.5"), unit="A")
    requirement = _req(SpecKey.OUTPUT_CURRENT_MAX, RequirementOperator.EQ, 500, unit="mA")
    assert evaluate_requirement(requirement, spec).status == ValidationStatus.PASS


def test_unit_normalization_temperature():
    spec = _spec(SpecKey.OPERATING_TEMP_MIN, numeric=Decimal("0"), unit="°C")
    requirement = _req(SpecKey.OPERATING_TEMP_MIN, RequirementOperator.EQ, 32, unit="°F")
    assert evaluate_requirement(requirement, spec).status == ValidationStatus.PASS


@pytest.mark.parametrize(
    ("actual", "expected"),
    [
        (Decimal("-20"), ValidationStatus.PASS),
        (Decimal("-30"), ValidationStatus.PASS),
        (Decimal("-10"), ValidationStatus.FAIL),
    ],
)
def test_operating_temp_min_lte(actual, expected):
    spec = _spec(SpecKey.OPERATING_TEMP_MIN, numeric=actual, unit="°C")
    requirement = _req(SpecKey.OPERATING_TEMP_MIN, RequirementOperator.LTE, -20, unit="°C")
    assert evaluate_requirement(requirement, spec).status == expected


def test_missing_specifications_unknown():
    requirement = _req(SpecKey.ETHERNET_PORTS, RequirementOperator.GTE, 5)
    assert evaluate_requirement(requirement, None).status == ValidationStatus.UNKNOWN

    bool_req = _req(SpecKey.DIN_RAIL_MOUNTABLE, RequirementOperator.EQ, True)
    assert evaluate_requirement(bool_req, None).status == ValidationStatus.UNKNOWN

    text_req = _req(SpecKey.MOUNTING, RequirementOperator.CONTAINS, "DIN rail")
    assert evaluate_requirement(text_req, None).status == ValidationStatus.UNKNOWN


def test_missing_boolean_not_false():
    requirement = _req(SpecKey.DIN_RAIL_MOUNTABLE, RequirementOperator.EQ, True)
    result = evaluate_requirement(requirement, None)
    assert result.status == ValidationStatus.UNKNOWN
    assert result.actual_value is None


def test_missing_numeric_not_zero():
    requirement = _req(SpecKey.ETHERNET_PORTS, RequirementOperator.GTE, 5)
    result = evaluate_requirement(requirement, None)
    assert result.status == ValidationStatus.UNKNOWN
    assert result.actual_value is None


def test_invalid_numeric_text_unknown():
    spec = _spec(SpecKey.ETHERNET_PORTS, text="five")
    requirement = _req(SpecKey.ETHERNET_PORTS, RequirementOperator.GTE, 5)
    assert evaluate_requirement(requirement, spec).status == ValidationStatus.UNKNOWN


def test_invalid_unit_unknown():
    spec = _spec(SpecKey.INPUT_VOLTAGE, numeric=Decimal("24"), unit="industrial")
    requirement = _req(SpecKey.INPUT_VOLTAGE, RequirementOperator.EQ, 24, unit="V")
    assert evaluate_requirement(requirement, spec).status == ValidationStatus.UNKNOWN


def test_overall_status_rules():
    requirements = [
        _req(SpecKey.INPUT_VOLTAGE, RequirementOperator.EQ, 24, unit="V"),
        _req(SpecKey.ETHERNET_PORTS, RequirementOperator.GTE, 5),
        _req(SpecKey.DIN_RAIL_MOUNTABLE, RequirementOperator.EQ, True),
    ]
    pass_results = [
        evaluate_requirement(
            requirements[0],
            _spec(SpecKey.INPUT_VOLTAGE, numeric=Decimal("24"), unit="V"),
        ),
        evaluate_requirement(
            requirements[1],
            _spec(SpecKey.ETHERNET_PORTS, numeric=Decimal("5")),
        ),
        evaluate_requirement(
            requirements[2],
            _spec(SpecKey.DIN_RAIL_MOUNTABLE, boolean=True),
        ),
    ]
    assert compute_overall_status(requirements, pass_results) == ValidationStatus.PASS

    fail_results = [
        pass_results[0],
        evaluate_requirement(requirements[1], _spec(SpecKey.ETHERNET_PORTS, numeric=Decimal("3"))),
        pass_results[2],
    ]
    assert compute_overall_status(requirements, fail_results) == ValidationStatus.FAIL

    unknown_results = [
        pass_results[0],
        evaluate_requirement(requirements[1], None),
        pass_results[2],
    ]
    assert compute_overall_status(requirements, unknown_results) == ValidationStatus.UNKNOWN

    mixed_results = [
        pass_results[0],
        evaluate_requirement(requirements[1], None),
        evaluate_requirement(requirements[2], _spec(SpecKey.DIN_RAIL_MOUNTABLE, boolean=False)),
    ]
    assert compute_overall_status(requirements, mixed_results) == ValidationStatus.FAIL


def test_preferred_requirements_do_not_affect_overall():
    requirements = [
        _req(SpecKey.ETHERNET_PORTS, RequirementOperator.GTE, 5),
        _req(
            SpecKey.IP_RATING,
            RequirementOperator.CONTAINS,
            "IP67",
            required=False,
            priority=RequirementPriority.PREFERRED,
        ),
    ]
    results = [
        evaluate_requirement(requirements[0], _spec(SpecKey.ETHERNET_PORTS, numeric=Decimal("8"))),
        evaluate_requirement(requirements[1], _spec(SpecKey.IP_RATING, text="IP54")),
    ]
    assert results[1].status == ValidationStatus.FAIL
    assert compute_overall_status(requirements, results) == ValidationStatus.PASS

    unknown_preferred = [
        evaluate_requirement(requirements[0], _spec(SpecKey.ETHERNET_PORTS, numeric=Decimal("8"))),
        evaluate_requirement(requirements[1], None),
    ]
    assert compute_overall_status(requirements, unknown_preferred) == ValidationStatus.PASS


DEMO_REQUIREMENTS = [
    StructuredRequirement(
        spec_key=SpecKey.INPUT_VOLTAGE,
        operator=RequirementOperator.EQ,
        value=24,
        unit="V",
        source_text="24 VDC power",
    ),
    StructuredRequirement(
        spec_key=SpecKey.ETHERNET_PORTS,
        operator=RequirementOperator.GTE,
        value=5,
        source_text="minimum 5 Ethernet ports",
    ),
    StructuredRequirement(
        spec_key=SpecKey.DIN_RAIL_MOUNTABLE,
        operator=RequirementOperator.EQ,
        value=True,
        source_text="DIN rail mounting",
    ),
    StructuredRequirement(
        spec_key=SpecKey.SUPPORTS_MODBUS_TCP,
        operator=RequirementOperator.EQ,
        value=True,
        source_text="Modbus TCP support",
    ),
    StructuredRequirement(
        spec_key=SpecKey.OPERATING_TEMP_MIN,
        operator=RequirementOperator.LTE,
        value=-20,
        unit="°C",
        source_text="operating temperature down to -20°C",
    ),
]


@pytest.mark.asyncio
async def test_ceo_demo_products(db_session):
    await seed_catalog(db_session)

    async def validate_model(model_number: str):
        product = await db_session.scalar(
            select(Product)
            .options(selectinload(Product.specifications))
            .where(Product.model_number == model_number),
        )
        assert product is not None
        return validate_product(product, DEMO_REQUIREMENTS)

    pass_result = await validate_model("NS-SW-005")
    assert pass_result.status == ValidationStatus.PASS
    assert all(item.status == ValidationStatus.PASS for item in pass_result.results)

    fail_result = await validate_model("VIS-SW-003")
    assert fail_result.status == ValidationStatus.FAIL
    ports = next(item for item in fail_result.results if item.spec_key == SpecKey.ETHERNET_PORTS)
    assert ports.status == ValidationStatus.FAIL

    unknown_result = await validate_model("AC-SW-008")
    assert unknown_result.status == ValidationStatus.UNKNOWN
    temp = next(
        item for item in unknown_result.results if item.spec_key == SpecKey.OPERATING_TEMP_MIN
    )
    assert temp.status == ValidationStatus.UNKNOWN
    assert temp.actual_value is None


@pytest.mark.asyncio
async def test_validation_api_single_product(seeded_client):
    products = await seeded_client.get("/api/v1/products", params={"model_number": "NS-SW-005"})
    product_id = products.json()["items"][0]["id"]

    response = await seeded_client.post(
        f"/api/v1/validation/products/{product_id}",
        json={"requirements": [req.model_dump(mode="json") for req in DEMO_REQUIREMENTS]},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["model_number"] == "NS-SW-005"
    assert payload["status"] == "PASS"
    assert len(payload["results"]) == 5


@pytest.mark.asyncio
async def test_validation_api_multi_product(seeded_client):
    product_ids = []
    for model_number in ("NS-SW-005", "VIS-SW-003", "AC-SW-008"):
        response = await seeded_client.get(
            "/api/v1/products",
            params={"model_number": model_number},
        )
        product_ids.append(response.json()["items"][0]["id"])

    response = await seeded_client.post(
        "/api/v1/validation/products",
        json={
            "product_ids": product_ids,
            "requirements": [req.model_dump(mode="json") for req in DEMO_REQUIREMENTS],
        },
    )
    assert response.status_code == 200
    statuses = {item["model_number"]: item["status"] for item in response.json()["results"]}
    assert statuses == {
        "NS-SW-005": "PASS",
        "VIS-SW-003": "FAIL",
        "AC-SW-008": "UNKNOWN",
    }


@pytest.mark.asyncio
async def test_validation_api_product_not_found(seeded_client):
    response = await seeded_client.post(
        f"/api/v1/validation/products/{uuid4()}",
        json={"requirements": [DEMO_REQUIREMENTS[0].model_dump(mode="json")]},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_validation_api_malformed_requirements(seeded_client):
    products = await seeded_client.get("/api/v1/products", params={"model_number": "NS-SW-005"})
    product_id = products.json()["items"][0]["id"]

    response = await seeded_client.post(
        f"/api/v1/validation/products/{product_id}",
        json={"requirements": []},
    )
    assert response.status_code == 422
