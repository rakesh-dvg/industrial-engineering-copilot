"""Evidence retrieval linked to deterministic validation results."""

from __future__ import annotations

from enum import StrEnum

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.spec_keys import SpecKey
from app.embeddings.base import EmbeddingProvider
from app.models.product import Product
from app.schemas.evidence import (
    EvidenceItem,
    EvidenceStatus,
    ProductEvidenceResult,
    RequirementEvidenceResult,
)
from app.schemas.rfq import StructuredRequirement
from app.services.retrieval import retrieve_product_chunks
from app.services.validation import validate_product

SPEC_EVIDENCE_QUERIES: dict[SpecKey, str] = {
    SpecKey.INPUT_VOLTAGE: "input voltage VDC power supply electrical",
    SpecKey.OUTPUT_VOLTAGE: "output voltage power supply",
    SpecKey.OUTPUT_CURRENT_MAX: "output current maximum amperes",
    SpecKey.ETHERNET_PORTS: "Ethernet ports network interface",
    SpecKey.DIN_RAIL_MOUNTABLE: "DIN rail mounting mechanical installation",
    SpecKey.SUPPORTS_MODBUS_TCP: "Modbus TCP protocol communication",
    SpecKey.OPERATING_TEMP_MIN: "operating temperature minimum environmental",
    SpecKey.OPERATING_TEMP_MAX: "operating temperature maximum environmental",
    SpecKey.MOUNTING: "mounting installation mechanical",
    SpecKey.IP_RATING: "IP rating ingress protection",
}


def build_requirement_query(requirement: StructuredRequirement) -> str:
    base = SPEC_EVIDENCE_QUERIES.get(
        requirement.spec_key,
        requirement.spec_key.value.replace("_", " "),
    )
    parts = [base]
    if requirement.source_text:
        parts.append(requirement.source_text)
    if requirement.value is not None:
        parts.append(str(requirement.value))
    if requirement.unit:
        parts.append(requirement.unit)
    return " ".join(parts)


def _evidence_status(requirement_status: StrEnum, items: list[EvidenceItem]) -> EvidenceStatus:
    if items:
        return EvidenceStatus.FOUND
    if requirement_status.value == "UNKNOWN":
        return EvidenceStatus.INSUFFICIENT
    return EvidenceStatus.NOT_FOUND


async def get_product_evidence(
    session: AsyncSession,
    product: Product,
    requirements: list[StructuredRequirement],
    *,
    embedder: EmbeddingProvider,
    top_k: int = 2,
) -> ProductEvidenceResult:
    validation = validate_product(product, requirements)
    requirement_results: list[RequirementEvidenceResult] = []

    for requirement, validation_result in zip(requirements, validation.results, strict=True):
        retrieved = await retrieve_product_chunks(
            session,
            product_id=product.id,
            query=build_requirement_query(requirement),
            embedder=embedder,
            top_k=top_k,
        )
        evidence_items = [
            EvidenceItem(
                text=item.text,
                page_number=item.page_number,
                document_id=item.document_id,
                chunk_id=item.chunk_id,
                document_title=item.document_title,
                document_filename=item.document_filename,
                similarity_score=item.similarity_score,
            )
            for item in retrieved
        ]
        requirement_results.append(
            RequirementEvidenceResult(
                spec_key=validation_result.spec_key,
                operator=validation_result.operator,
                required=validation_result.required,
                priority=validation_result.priority,
                status=validation_result.status,
                required_value=validation_result.required_value,
                required_unit=validation_result.required_unit,
                actual_value=validation_result.actual_value,
                actual_unit=validation_result.actual_unit,
                details=validation_result.details,
                source_text=validation_result.source_text,
                evidence_status=_evidence_status(validation_result.status, evidence_items),
                evidence=evidence_items,
            ),
        )

    return ProductEvidenceResult(
        product_id=validation.product_id,
        model_number=validation.model_number,
        status=validation.status,
        requirements=requirement_results,
    )
