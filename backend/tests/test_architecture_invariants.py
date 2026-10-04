"""Phase 9 architecture invariant regression tests."""

from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.domain.spec_keys import SpecKey
from app.embeddings.deps import get_embedding_provider
from app.models.product import Product
from app.models.product_specification import ProductSpecification
from app.schemas.validation import ValidationStatus
from app.seed.catalog import seed_catalog
from app.seed.documents import seed_product_datasheets
from app.services.evidence import get_product_evidence
from app.services.recommendation import build_recommendation_result, recommend_products
from app.services.validation import validate_product
from tests.test_recommendation import _evidence_for_product, _pass_specs, _product
from tests.test_validation import DEMO_REQUIREMENTS


@pytest.mark.asyncio
async def test_pass_without_evidence_remains_eligible(db_session):
    await seed_catalog(db_session)
    product = await db_session.scalar(
        select(Product)
        .options(
            selectinload(Product.manufacturer),
            selectinload(Product.category),
            selectinload(Product.specifications),
            selectinload(Product.pricing),
        )
        .where(Product.model_number == "NS-SW-005"),
    )
    assert product is not None

    validation = validate_product(product, DEMO_REQUIREMENTS)
    assert validation.status == ValidationStatus.PASS

    result = await recommend_products(
        db_session,
        [product],
        DEMO_REQUIREMENTS,
        embedder=get_embedding_provider(),
    )
    assert result.primary_recommendation is not None
    assert result.primary_recommendation.validation_status == ValidationStatus.PASS
    assert result.primary_recommendation.model_number == "NS-SW-005"


def test_pass_without_evidence_is_not_fail():
    product = _product(
        model_number="PASS-NO-EVIDENCE",
        unit_price=Decimal("185"),
        lead_time_days=14,
        specifications=_pass_specs(),
    )
    validation = validate_product(product, DEMO_REQUIREMENTS[:2])
    assert validation.status == ValidationStatus.PASS

    result = build_recommendation_result(
        [product],
        [validation],
        [_evidence_for_product(product, supported_keys=set())],
        DEMO_REQUIREMENTS[:2],
    )
    assert result.primary_recommendation is not None
    assert result.primary_recommendation.validation_status != ValidationStatus.FAIL


@pytest.mark.asyncio
async def test_evidence_does_not_change_validation_status(db_session):
    await seed_catalog(db_session)
    await seed_product_datasheets(db_session)
    product = await db_session.scalar(
        select(Product)
        .options(selectinload(Product.specifications))
        .where(Product.model_number == "VIS-SW-003"),
    )
    assert product is not None

    validation = validate_product(product, DEMO_REQUIREMENTS)
    assert validation.status == ValidationStatus.FAIL

    evidence = await get_product_evidence(
        db_session,
        product,
        DEMO_REQUIREMENTS,
        embedder=get_embedding_provider(),
    )
    assert evidence.status == ValidationStatus.FAIL
    assert validation.status == ValidationStatus.FAIL


def test_fail_and_unknown_never_primary_recommendation():
    fail_product = _product(
        model_number="FAIL-001",
        unit_price=Decimal("100"),
        lead_time_days=10,
        specifications=[
            ProductSpecification(
                id=uuid4(),
                product_id=uuid4(),
                spec_key=SpecKey.ETHERNET_PORTS.value,
                numeric_value=Decimal("3"),
            ),
        ],
    )
    unknown_product = _product(
        model_number="UNKNOWN-001",
        unit_price=Decimal("100"),
        lead_time_days=10,
        specifications=[
            ProductSpecification(
                id=uuid4(),
                product_id=uuid4(),
                spec_key=SpecKey.ETHERNET_PORTS.value,
                numeric_value=Decimal("8"),
            ),
        ],
    )
    pass_product = _product(
        model_number="PASS-001",
        unit_price=Decimal("185"),
        lead_time_days=14,
        specifications=_pass_specs(),
    )

    fail_validation = validate_product(fail_product, DEMO_REQUIREMENTS[:2])
    unknown_validation = validate_product(unknown_product, DEMO_REQUIREMENTS[:2])
    pass_validation = validate_product(pass_product, DEMO_REQUIREMENTS[:2])

    assert fail_validation.status == ValidationStatus.FAIL
    assert unknown_validation.status == ValidationStatus.UNKNOWN
    assert pass_validation.status == ValidationStatus.PASS

    result = build_recommendation_result(
        [fail_product, unknown_product, pass_product],
        [fail_validation, unknown_validation, pass_validation],
        [
            _evidence_for_product(fail_product, supported_keys=set(SpecKey)),
            _evidence_for_product(unknown_product, supported_keys=set(SpecKey)),
            _evidence_for_product(
                pass_product,
                supported_keys={SpecKey.INPUT_VOLTAGE, SpecKey.ETHERNET_PORTS},
            ),
        ],
        DEMO_REQUIREMENTS[:2],
    )

    assert result.primary_recommendation is not None
    assert result.primary_recommendation.model_number == "PASS-001"
    excluded = {item.model_number: item.validation_status for item in result.excluded_products}
    assert excluded["FAIL-001"] == ValidationStatus.FAIL
    assert excluded["UNKNOWN-001"] == ValidationStatus.UNKNOWN


def test_recommendation_ordering_is_deterministic():
    cheaper = _product(
        model_number="PASS-CHEAP",
        unit_price=Decimal("150"),
        lead_time_days=21,
        specifications=_pass_specs(),
    )
    premium = _product(
        model_number="PASS-PREMIUM",
        unit_price=Decimal("185"),
        lead_time_days=14,
        specifications=_pass_specs(),
    )

    validations = [
        validate_product(cheaper, DEMO_REQUIREMENTS[:2]),
        validate_product(premium, DEMO_REQUIREMENTS[:2]),
    ]
    evidence = [
        _evidence_for_product(
            cheaper,
            supported_keys={SpecKey.INPUT_VOLTAGE, SpecKey.ETHERNET_PORTS},
        ),
        _evidence_for_product(
            premium,
            supported_keys={SpecKey.INPUT_VOLTAGE, SpecKey.ETHERNET_PORTS},
        ),
    ]

    first = build_recommendation_result(
        [cheaper, premium],
        validations,
        evidence,
        DEMO_REQUIREMENTS[:2],
    )
    second = build_recommendation_result(
        [cheaper, premium],
        validations,
        evidence,
        DEMO_REQUIREMENTS[:2],
    )

    assert first.primary_recommendation is not None
    assert second.primary_recommendation is not None
    assert (
        first.primary_recommendation.model_number
        == second.primary_recommendation.model_number
    )
    assert first.primary_recommendation.recommendation_score == (
        second.primary_recommendation.recommendation_score
    )
