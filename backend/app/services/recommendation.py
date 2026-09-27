"""Deterministic product recommendation (Phase 5A)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.embeddings.base import EmbeddingProvider
from app.models.product import Product
from app.schemas.evidence import ProductEvidenceResult
from app.schemas.recommendation import (
    EvidenceCoverage,
    ExcludedProduct,
    RecommendationItem,
    RecommendationResult,
)
from app.schemas.rfq import StructuredRequirement
from app.schemas.validation import ProductValidationResult, ValidationStatus
from app.services.evidence import get_product_evidence
from app.services.validation import is_must_have, validate_product

FAIL_EXCLUSION_REASON = (
    "Does not satisfy one or more required engineering constraints"
)
UNKNOWN_EXCLUSION_REASON = (
    "Technical validation is incomplete because one or more required "
    "specifications are undocumented"
)
SINGLE_PASS_REASON = "Only product satisfying all required engineering constraints."


@dataclass(frozen=True)
class _RankedEligible:
    product: Product
    validation: ProductValidationResult
    evidence: ProductEvidenceResult
    evidence_supported: int
    evidence_required: int
    evidence_ratio: float
    price_score: float
    lead_time_score: float
    recommendation_score: int


def requirements_summary(requirements: list[StructuredRequirement]) -> str:
    required_count = sum(1 for requirement in requirements if is_must_have(requirement))
    if required_count == 1:
        return "1 required engineering constraint"
    return f"{required_count} required engineering constraints"


def evidence_coverage_counts(
    evidence: ProductEvidenceResult,
    requirements: list[StructuredRequirement],
) -> tuple[int, int]:
    evidence_by_key = {item.spec_key: item for item in evidence.requirements}
    required_count = 0
    supported_count = 0
    for requirement in requirements:
        if not is_must_have(requirement):
            continue
        required_count += 1
        item = evidence_by_key.get(requirement.spec_key)
        if item is not None and item.evidence:
            supported_count += 1
    return supported_count, required_count


def _normalize_lower_is_better(values: dict[UUID, Decimal | int], product_id: UUID) -> float:
    if not values:
        return 1.0
    numbers = list(values.values())
    minimum = min(numbers)
    maximum = max(numbers)
    if minimum == maximum:
        return 1.0
    value = values[product_id]
    return float((maximum - value) / (maximum - minimum))


def compute_recommendation_score(
    evidence_ratio: float,
    price_score: float,
    lead_time_score: float,
) -> int:
    score = 50 + (20 * evidence_ratio) + (15 * price_score) + (15 * lead_time_score)
    return round(score)


def _format_price(amount: Decimal, currency: str) -> str:
    return f"{currency} {amount:.2f}"


def _first_must_have_detail(
    requirements: list[StructuredRequirement],
    validation: ProductValidationResult,
    *,
    status: ValidationStatus,
) -> str | None:
    for requirement, result in zip(requirements, validation.results, strict=True):
        if not is_must_have(requirement):
            continue
        if result.status == status:
            return result.details
    return None


def build_exclusion_reason(
    requirements: list[StructuredRequirement],
    validation: ProductValidationResult,
) -> str:
    if validation.status == ValidationStatus.FAIL:
        detail = _first_must_have_detail(
            requirements,
            validation,
            status=ValidationStatus.FAIL,
        )
        return detail or FAIL_EXCLUSION_REASON
    detail = _first_must_have_detail(
        requirements,
        validation,
        status=ValidationStatus.UNKNOWN,
    )
    return detail or UNKNOWN_EXCLUSION_REASON


def build_recommendation_reasons(
    *,
    single_eligible: bool,
    evidence_supported: int,
    evidence_required: int,
    unit_price: Decimal | None,
    currency: str | None,
    lead_time_days: int | None,
) -> list[str]:
    if single_eligible:
        return [SINGLE_PASS_REASON]

    reasons = ["Satisfies all required engineering constraints"]
    if evidence_required == 0:
        pass
    elif evidence_supported == evidence_required:
        reasons.append("Technical evidence supports all required specifications")
    elif evidence_supported > 0:
        reasons.append(
            "Technical evidence supports "
            f"{evidence_supported} of {evidence_required} required specifications",
        )
    else:
        reasons.append("Technical evidence coverage is incomplete")

    if unit_price is not None and currency is not None:
        reasons.append(f"{_format_price(unit_price, currency)} unit price")
    if lead_time_days is not None:
        reasons.append(f"{lead_time_days}-day lead time")
    return reasons


def rank_eligible_products(
    eligible: list[_RankedEligible],
) -> list[_RankedEligible]:
    return sorted(
        eligible,
        key=lambda item: (
            -item.recommendation_score,
            item.product.model_number,
        ),
    )


def build_ranked_eligible_candidates(
    products: list[Product],
    validations: list[ProductValidationResult],
    evidence_results: list[ProductEvidenceResult],
    requirements: list[StructuredRequirement],
) -> list[_RankedEligible]:
    validation_by_id = {item.product_id: item for item in validations}
    evidence_by_id = {item.product_id: item for item in evidence_results}

    pass_products = [
        product
        for product in products
        if validation_by_id[product.id].status == ValidationStatus.PASS
    ]
    if not pass_products:
        return []

    prices: dict[UUID, Decimal] = {}
    lead_times: dict[UUID, int] = {}
    for product in pass_products:
        if product.pricing is not None:
            prices[product.id] = product.pricing.unit_price
            lead_times[product.id] = product.pricing.lead_time_days

    ranked: list[_RankedEligible] = []
    for product in pass_products:
        validation = validation_by_id[product.id]
        evidence = evidence_by_id[product.id]
        supported, required = evidence_coverage_counts(evidence, requirements)
        evidence_ratio = supported / required if required else 0.0
        price_score = _normalize_lower_is_better(prices, product.id) if prices else 0.0
        lead_time_score = (
            _normalize_lower_is_better(lead_times, product.id) if lead_times else 0.0
        )
        recommendation_score = compute_recommendation_score(
            evidence_ratio,
            price_score,
            lead_time_score,
        )
        ranked.append(
            _RankedEligible(
                product=product,
                validation=validation,
                evidence=evidence,
                evidence_supported=supported,
                evidence_required=required,
                evidence_ratio=evidence_ratio,
                price_score=price_score,
                lead_time_score=lead_time_score,
                recommendation_score=recommendation_score,
            ),
        )
    return rank_eligible_products(ranked)


def _to_recommendation_item(
    ranked: _RankedEligible,
    *,
    single_eligible: bool,
) -> RecommendationItem:
    pricing = ranked.product.pricing
    unit_price = pricing.unit_price if pricing is not None else None
    currency = pricing.currency if pricing is not None else None
    lead_time_days = pricing.lead_time_days if pricing is not None else None
    return RecommendationItem(
        product_id=ranked.product.id,
        model_number=ranked.product.model_number,
        manufacturer_name=ranked.product.manufacturer.name,
        product_name=ranked.product.name,
        validation_status=ValidationStatus.PASS,
        recommendation_score=ranked.recommendation_score,
        evidence_coverage=EvidenceCoverage(
            supported=ranked.evidence_supported,
            required=ranked.evidence_required,
        ),
        unit_price=f"{unit_price:.2f}" if unit_price is not None else None,
        currency=currency,
        lead_time_days=lead_time_days,
        reasons=build_recommendation_reasons(
            single_eligible=single_eligible,
            evidence_supported=ranked.evidence_supported,
            evidence_required=ranked.evidence_required,
            unit_price=unit_price,
            currency=currency,
            lead_time_days=lead_time_days,
        ),
    )


def build_recommendation_result(
    products: list[Product],
    validations: list[ProductValidationResult],
    evidence_results: list[ProductEvidenceResult],
    requirements: list[StructuredRequirement],
) -> RecommendationResult:
    validation_by_id = {item.product_id: item for item in validations}
    ranked_eligible = build_ranked_eligible_candidates(
        products,
        validations,
        evidence_results,
        requirements,
    )
    excluded_products = [
        ExcludedProduct(
            product_id=product.id,
            model_number=product.model_number,
            validation_status=validation_by_id[product.id].status,
            reason=build_exclusion_reason(requirements, validation_by_id[product.id]),
        )
        for product in products
        if validation_by_id[product.id].status != ValidationStatus.PASS
    ]

    primary: RecommendationItem | None = None
    alternatives: list[RecommendationItem] = []
    message: str | None = None
    single_eligible = len(ranked_eligible) == 1

    if ranked_eligible:
        primary = _to_recommendation_item(ranked_eligible[0], single_eligible=single_eligible)
        alternatives = [
            _to_recommendation_item(item, single_eligible=False)
            for item in ranked_eligible[1:]
        ]
    else:
        message = "No technically eligible product was found."

    return RecommendationResult(
        requirements_summary=requirements_summary(requirements),
        candidate_count=len(products),
        eligible_count=len(ranked_eligible),
        primary_recommendation=primary,
        alternatives=alternatives,
        excluded_products=excluded_products,
        message=message,
    )


async def recommend_products(
    session: AsyncSession,
    products: list[Product],
    requirements: list[StructuredRequirement],
    *,
    embedder: EmbeddingProvider,
) -> RecommendationResult:
    validations = [validate_product(product, requirements) for product in products]
    evidence_results: list[ProductEvidenceResult] = []
    for product in products:
        evidence_results.append(
            await get_product_evidence(
                session,
                product,
                requirements,
                embedder=embedder,
            ),
        )
    return build_recommendation_result(
        products,
        validations,
        evidence_results,
        requirements,
    )
