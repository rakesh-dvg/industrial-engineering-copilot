"""Phase 5A deterministic product recommendation tests."""

from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.domain.spec_keys import SpecKey
from app.models.manufacturer import Manufacturer
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.product_pricing import ProductPricing
from app.models.product_specification import ProductSpecification
from app.schemas.evidence import (
    EvidenceItem,
    EvidenceStatus,
    ProductEvidenceResult,
    RequirementEvidenceResult,
)
from app.schemas.rfq import RequirementPriority
from app.schemas.validation import ValidationStatus
from app.seed.catalog import seed_catalog
from app.services.recommendation import (
    FAIL_EXCLUSION_REASON,
    SINGLE_PASS_REASON,
    UNKNOWN_EXCLUSION_REASON,
    build_exclusion_reason,
    build_ranked_eligible_candidates,
    build_recommendation_result,
    compute_recommendation_score,
    evidence_coverage_counts,
    recommend_products,
)
from app.services.validation import validate_product
from tests.test_validation import DEMO_REQUIREMENTS


def _product(
    *,
    model_number: str,
    unit_price: Decimal,
    lead_time_days: int,
    specifications: list[ProductSpecification],
) -> Product:
    manufacturer = Manufacturer(id=uuid4(), name=f"M-{model_number}", is_active=True)
    category = ProductCategory(
        id=uuid4(),
        name="Switch",
        slug="switch",
        is_active=True,
    )
    product = Product(
        id=uuid4(),
        model_number=model_number,
        name=f"Switch {model_number}",
        is_active=True,
        manufacturer=manufacturer,
        category=category,
        specifications=specifications,
    )
    product.pricing = ProductPricing(
        id=uuid4(),
        product_id=product.id,
        unit_price=unit_price,
        currency="USD",
        discount_percent=Decimal("0"),
        lead_time_days=lead_time_days,
        is_active=True,
    )
    return product


def _pass_specs() -> list[ProductSpecification]:
    return [
        ProductSpecification(
            id=uuid4(),
            product_id=uuid4(),
            spec_key=SpecKey.INPUT_VOLTAGE.value,
            numeric_value=Decimal("24"),
            unit="V",
        ),
        ProductSpecification(
            id=uuid4(),
            product_id=uuid4(),
            spec_key=SpecKey.ETHERNET_PORTS.value,
            numeric_value=Decimal("8"),
        ),
    ]


def _evidence_for_product(
    product: Product,
    *,
    supported_keys: set[SpecKey],
) -> ProductEvidenceResult:
    requirements = []
    for requirement in DEMO_REQUIREMENTS[:2]:
        has_evidence = requirement.spec_key in supported_keys
        requirements.append(
            RequirementEvidenceResult(
                spec_key=requirement.spec_key,
                operator=requirement.operator,
                required=True,
                priority=RequirementPriority.MUST_HAVE,
                status=ValidationStatus.PASS,
                details="pass",
                evidence_status=EvidenceStatus.FOUND if has_evidence else EvidenceStatus.NOT_FOUND,
                evidence=[
                    EvidenceItem(
                        text="evidence",
                        page_number=1,
                        document_id=uuid4(),
                        chunk_id=uuid4(),
                        document_title="Datasheet",
                        document_filename="datasheet.txt",
                        similarity_score=0.8,
                    ),
                ]
                if has_evidence
                else [],
            ),
        )
    return ProductEvidenceResult(
        product_id=product.id,
        model_number=product.model_number,
        status=ValidationStatus.PASS,
        requirements=requirements,
    )


def test_pass_product_becomes_eligible():
    product = _product(
        model_number="PASS-001",
        unit_price=Decimal("100"),
        lead_time_days=10,
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
    assert result.eligible_count == 1
    assert result.primary_recommendation is not None
    assert result.primary_recommendation.validation_status == ValidationStatus.PASS


def test_fail_product_cannot_be_primary():
    product = _product(
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
    validation = validate_product(product, DEMO_REQUIREMENTS[:2])
    assert validation.status == ValidationStatus.FAIL

    result = build_recommendation_result(
        [product],
        [validation],
        [_evidence_for_product(product, supported_keys=set())],
        DEMO_REQUIREMENTS[:2],
    )
    assert result.primary_recommendation is None
    assert result.excluded_products[0].validation_status == ValidationStatus.FAIL
    assert (
        FAIL_EXCLUSION_REASON in result.excluded_products[0].reason
        or "ethernet" in result.excluded_products[0].reason.lower()
    )


def test_unknown_product_cannot_be_primary():
    product = _product(
        model_number="UNK-001",
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
    validation = validate_product(product, DEMO_REQUIREMENTS[:2])
    assert validation.status == ValidationStatus.UNKNOWN

    result = build_recommendation_result(
        [product],
        [validation],
        [_evidence_for_product(product, supported_keys=set())],
        DEMO_REQUIREMENTS[:2],
    )
    assert result.primary_recommendation is None
    assert result.excluded_products[0].validation_status == ValidationStatus.UNKNOWN
    assert (
        UNKNOWN_EXCLUSION_REASON in result.excluded_products[0].reason
        or "does not contain" in result.excluded_products[0].reason.lower()
    )


def test_no_pass_products_returns_no_recommendation():
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
    validation = validate_product(fail_product, DEMO_REQUIREMENTS[:2])
    result = build_recommendation_result(
        [fail_product],
        [validation],
        [_evidence_for_product(fail_product, supported_keys=set())],
        DEMO_REQUIREMENTS[:2],
    )
    assert result.primary_recommendation is None
    assert result.message == "No technically eligible product was found."


def test_one_pass_product_becomes_primary_with_single_reason():
    product = _product(
        model_number="PASS-001",
        unit_price=Decimal("185"),
        lead_time_days=14,
        specifications=_pass_specs(),
    )
    validation = validate_product(product, DEMO_REQUIREMENTS[:2])
    result = build_recommendation_result(
        [product],
        [validation],
        [
            _evidence_for_product(
                product,
                supported_keys={SpecKey.INPUT_VOLTAGE, SpecKey.ETHERNET_PORTS},
            ),
        ],
        DEMO_REQUIREMENTS[:2],
    )
    assert result.primary_recommendation is not None
    assert result.primary_recommendation.reasons == [SINGLE_PASS_REASON]


def test_multiple_pass_products_ranked_deterministically():
    cheaper = _product(
        model_number="CHEAP-001",
        unit_price=Decimal("100"),
        lead_time_days=21,
        specifications=_pass_specs(),
    )
    premium = _product(
        model_number="PREM-001",
        unit_price=Decimal("200"),
        lead_time_days=7,
        specifications=_pass_specs(),
    )
    validations = [
        validate_product(cheaper, DEMO_REQUIREMENTS[:2]),
        validate_product(premium, DEMO_REQUIREMENTS[:2]),
    ]
    evidence = [
        _evidence_for_product(cheaper, supported_keys={SpecKey.INPUT_VOLTAGE}),
        _evidence_for_product(
            premium,
            supported_keys={SpecKey.INPUT_VOLTAGE, SpecKey.ETHERNET_PORTS},
        ),
    ]
    result = build_recommendation_result(
        [cheaper, premium],
        validations,
        evidence,
        DEMO_REQUIREMENTS[:2],
    )
    assert result.primary_recommendation is not None
    assert result.primary_recommendation.model_number == "PREM-001"
    assert len(result.alternatives) == 1
    assert result.alternatives[0].model_number == "CHEAP-001"


def test_evidence_coverage_affects_ranking():
    low_evidence = _product(
        model_number="LOW-EVID",
        unit_price=Decimal("150"),
        lead_time_days=14,
        specifications=_pass_specs(),
    )
    high_evidence = _product(
        model_number="HIGH-EVID",
        unit_price=Decimal("150"),
        lead_time_days=14,
        specifications=_pass_specs(),
    )
    validations = [
        validate_product(low_evidence, DEMO_REQUIREMENTS[:2]),
        validate_product(high_evidence, DEMO_REQUIREMENTS[:2]),
    ]
    evidence = [
        _evidence_for_product(low_evidence, supported_keys=set()),
        _evidence_for_product(
            high_evidence,
            supported_keys={SpecKey.INPUT_VOLTAGE, SpecKey.ETHERNET_PORTS},
        ),
    ]
    ranked = build_ranked_eligible_candidates(
        [low_evidence, high_evidence],
        validations,
        evidence,
        DEMO_REQUIREMENTS[:2],
    )
    assert ranked[0].product.model_number == "HIGH-EVID"


def test_lower_price_improves_ranking_when_other_factors_equal():
    cheaper = _product(
        model_number="CHEAP",
        unit_price=Decimal("100"),
        lead_time_days=14,
        specifications=_pass_specs(),
    )
    expensive = _product(
        model_number="EXPENSIVE",
        unit_price=Decimal("250"),
        lead_time_days=14,
        specifications=_pass_specs(),
    )
    validations = [
        validate_product(cheaper, DEMO_REQUIREMENTS[:2]),
        validate_product(expensive, DEMO_REQUIREMENTS[:2]),
    ]
    evidence = [
        _evidence_for_product(
            cheaper,
            supported_keys={SpecKey.INPUT_VOLTAGE, SpecKey.ETHERNET_PORTS},
        ),
        _evidence_for_product(
            expensive,
            supported_keys={SpecKey.INPUT_VOLTAGE, SpecKey.ETHERNET_PORTS},
        ),
    ]
    ranked = build_ranked_eligible_candidates(
        [cheaper, expensive],
        validations,
        evidence,
        DEMO_REQUIREMENTS[:2],
    )
    assert ranked[0].product.model_number == "CHEAP"


def test_shorter_lead_time_improves_ranking_when_other_factors_equal():
    fast = _product(
        model_number="FAST",
        unit_price=Decimal("150"),
        lead_time_days=7,
        specifications=_pass_specs(),
    )
    slow = _product(
        model_number="SLOW",
        unit_price=Decimal("150"),
        lead_time_days=28,
        specifications=_pass_specs(),
    )
    validations = [
        validate_product(fast, DEMO_REQUIREMENTS[:2]),
        validate_product(slow, DEMO_REQUIREMENTS[:2]),
    ]
    evidence = [
        _evidence_for_product(fast, supported_keys={SpecKey.INPUT_VOLTAGE, SpecKey.ETHERNET_PORTS}),
        _evidence_for_product(slow, supported_keys={SpecKey.INPUT_VOLTAGE, SpecKey.ETHERNET_PORTS}),
    ]
    ranked = build_ranked_eligible_candidates(
        [fast, slow],
        validations,
        evidence,
        DEMO_REQUIREMENTS[:2],
    )
    assert ranked[0].product.model_number == "FAST"


def test_recommendation_reasons_are_deterministic():
    product = _product(
        model_number="PASS-001",
        unit_price=Decimal("185"),
        lead_time_days=14,
        specifications=_pass_specs(),
    )
    validation = validate_product(product, DEMO_REQUIREMENTS[:2])
    result = build_recommendation_result(
        [product],
        [validation],
        [
            _evidence_for_product(
                product,
                supported_keys={SpecKey.INPUT_VOLTAGE, SpecKey.ETHERNET_PORTS},
            ),
        ],
        DEMO_REQUIREMENTS[:2],
    )
    assert result.primary_recommendation is not None
    assert result.primary_recommendation.reasons == [SINGLE_PASS_REASON]


def test_recommendation_does_not_alter_validation_status():
    product = _product(
        model_number="PASS-001",
        unit_price=Decimal("100"),
        lead_time_days=10,
        specifications=_pass_specs(),
    )
    validation = validate_product(product, DEMO_REQUIREMENTS[:2])
    result = build_recommendation_result(
        [product],
        [validation],
        [_evidence_for_product(product, supported_keys=set())],
        DEMO_REQUIREMENTS[:2],
    )
    assert result.primary_recommendation is not None
    assert result.primary_recommendation.validation_status == validation.status


def test_compute_recommendation_score_is_integer():
    assert compute_recommendation_score(1.0, 1.0, 1.0) == 100
    assert isinstance(compute_recommendation_score(0.5, 0.5, 0.5), int)


def test_evidence_coverage_counts_required_only():
    product = _product(
        model_number="PASS-001",
        unit_price=Decimal("100"),
        lead_time_days=10,
        specifications=_pass_specs(),
    )
    evidence = _evidence_for_product(product, supported_keys={SpecKey.INPUT_VOLTAGE})
    supported, required = evidence_coverage_counts(evidence, DEMO_REQUIREMENTS[:2])
    assert required == 2
    assert supported == 1


def test_build_exclusion_reason_uses_validation_details():
    product = _product(
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
    validation = validate_product(product, DEMO_REQUIREMENTS[:2])
    reason = build_exclusion_reason(DEMO_REQUIREMENTS[:2], validation)
    assert "3" in reason or FAIL_EXCLUSION_REASON in reason


@pytest.mark.asyncio
async def test_ceo_demo_recommendation(seeded_client_with_documents):
    product_ids = []
    for model_number in ("NS-SW-005", "VIS-SW-003", "AC-SW-008"):
        response = await seeded_client_with_documents.get(
            "/api/v1/products",
            params={"model_number": model_number},
        )
        product_ids.append(response.json()["items"][0]["id"])

    response = await seeded_client_with_documents.post(
        "/api/v1/recommendations/products",
        json={
            "product_ids": product_ids,
            "requirements": [req.model_dump(mode="json") for req in DEMO_REQUIREMENTS],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["eligible_count"] == 1
    assert payload["primary_recommendation"]["model_number"] == "NS-SW-005"
    assert payload["primary_recommendation"]["validation_status"] == "PASS"
    excluded = {
        item["model_number"]: item["validation_status"]
        for item in payload["excluded_products"]
    }
    assert excluded == {
        "VIS-SW-003": "FAIL",
        "AC-SW-008": "UNKNOWN",
    }


@pytest.mark.asyncio
async def test_recommendation_api_empty_candidates(seeded_client):
    response = await seeded_client.post(
        "/api/v1/recommendations/products",
        json={
            "product_ids": [],
            "requirements": [DEMO_REQUIREMENTS[0].model_dump(mode="json")],
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "NO_RECOMMENDATION_CANDIDATES"


@pytest.mark.asyncio
async def test_recommendation_api_invalid_requirements(seeded_client):
    products = await seeded_client.get("/api/v1/products", params={"model_number": "NS-SW-005"})
    product_id = products.json()["items"][0]["id"]

    response = await seeded_client.post(
        "/api/v1/recommendations/products",
        json={"product_ids": [product_id], "requirements": []},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_recommendation_output_is_schema_valid(seeded_client_with_documents):
    product_ids = []
    for model_number in ("NS-SW-005", "VIS-SW-003", "AC-SW-008"):
        response = await seeded_client_with_documents.get(
            "/api/v1/products",
            params={"model_number": model_number},
        )
        product_ids.append(response.json()["items"][0]["id"])

    response = await seeded_client_with_documents.post(
        "/api/v1/recommendations/products",
        json={
            "product_ids": product_ids,
            "requirements": [req.model_dump(mode="json") for req in DEMO_REQUIREMENTS],
        },
    )
    assert response.status_code == 200
    primary = response.json()["primary_recommendation"]
    assert primary["unit_price"] == "185.00"
    assert primary["currency"] == "USD"
    assert primary["lead_time_days"] == 14


@pytest.mark.asyncio
async def test_recommendation_does_not_alter_quotation_rules(seeded_client_with_documents):
    fail_product = await seeded_client_with_documents.get(
        "/api/v1/products",
        params={"model_number": "VIS-SW-003"},
    )
    product_id = fail_product.json()["items"][0]["id"]

    response = await seeded_client_with_documents.post(
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
async def test_recommend_products_service(db_session):
    await seed_catalog(db_session)
    products = []
    for model_number in ("NS-SW-005", "VIS-SW-003", "AC-SW-008"):
        product = await db_session.scalar(
            select(Product)
            .options(
                selectinload(Product.manufacturer),
                selectinload(Product.category),
                selectinload(Product.specifications),
                selectinload(Product.pricing),
            )
            .where(Product.model_number == model_number),
        )
        assert product is not None
        products.append(product)

    from app.embeddings.deps import get_embedding_provider

    result = await recommend_products(
        db_session,
        products,
        DEMO_REQUIREMENTS,
        embedder=get_embedding_provider(),
    )
    assert result.primary_recommendation is not None
    assert result.primary_recommendation.model_number == "NS-SW-005"
