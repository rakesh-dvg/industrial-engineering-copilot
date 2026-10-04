"""Quotation creation and retrieval for Phase 7."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.embeddings.base import EmbeddingProvider
from app.models.quotation import Quotation, QuotationLineItem
from app.models.quotation import QuotationStatus as ModelQuotationStatus
from app.schemas.errors import ErrorDetail, ErrorResponse
from app.schemas.quotation import (
    CreateQuotationRequest,
    QuotationLineResponse,
    QuotationListResponse,
    QuotationResponse,
)
from app.schemas.quotation import (
    QuotationStatus as SchemaQuotationStatus,
)
from app.schemas.validation import ValidationStatus
from app.services.catalog import get_product_entity
from app.services.evidence import get_product_evidence
from app.services.quotation_calculation import calculate_line, calculate_quotation
from app.services.validation import validate_product


def _error(code: str, message: str, status_code: int) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail=ErrorResponse(error=ErrorDetail(code=code, message=message)).model_dump(),
    )


def _not_found(message: str) -> HTTPException:
    return _error("NOT_FOUND", message, status.HTTP_404_NOT_FOUND)


async def _next_quotation_number(session: AsyncSession) -> str:
    year = datetime.now(tz=UTC).year
    prefix = f"Q-{year}-"
    existing_numbers = set(
        await session.scalars(
            select(Quotation.quotation_number).where(
                Quotation.quotation_number.like(f"{prefix}%"),
            ),
        ),
    )
    sequence = 1
    while f"{prefix}{sequence:04d}" in existing_numbers:
        sequence += 1
    return f"{prefix}{sequence:04d}"


def _quotation_to_response(quotation: Quotation) -> QuotationResponse:
    return QuotationResponse(
        id=quotation.id,
        quotation_number=quotation.quotation_number,
        status=SchemaQuotationStatus(str(quotation.status)),
        customer_name=quotation.customer_name,
        customer_email=quotation.customer_email,
        customer_reference=quotation.customer_reference,
        title=quotation.title,
        currency=quotation.currency,
        validity_days=quotation.validity_days,
        lead_time_days=quotation.lead_time_days,
        technical_status=ValidationStatus(quotation.technical_status),
        subtotal=quotation.subtotal,
        discount_percent=quotation.discount_percent,
        discount_amount=quotation.discount_amount,
        total=quotation.total,
        lines=[
            QuotationLineResponse(
                id=line.id,
                product_id=line.product_id,
                model_number=line.model_number,
                description=line.description,
                quantity=line.quantity,
                unit_price=line.unit_price,
                currency=line.currency,
                discount_percent=line.discount_percent,
                line_subtotal=line.line_subtotal,
                line_total=line.line_total,
            )
            for line in sorted(quotation.lines, key=lambda item: item.created_at)
        ],
        validation_snapshot=quotation.validation_snapshot,
        evidence_snapshot=quotation.evidence_snapshot,
        created_at=quotation.created_at,
        updated_at=quotation.updated_at,
    )


async def _load_quotation(session: AsyncSession, quotation_id: UUID) -> Quotation:
    quotation = await session.scalar(
        select(Quotation)
        .options(selectinload(Quotation.lines))
        .where(Quotation.id == quotation_id),
    )
    if quotation is None:
        raise _not_found("Quotation not found.")
    return quotation


async def create_quotation(
    session: AsyncSession,
    request: CreateQuotationRequest,
    *,
    embedder: EmbeddingProvider | None = None,
) -> QuotationResponse:
    product = await get_product_entity(session, request.product_id)

    if product.pricing is None or not product.pricing.is_active:
        raise _error(
            "PRICING_NOT_FOUND",
            "Active catalog pricing was not found for the selected product.",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    validation = validate_product(product, request.requirements)
    if validation.status == ValidationStatus.FAIL:
        raise _error(
            "QUOTATION_VALIDATION_FAILED",
            "Product failed required technical validation and cannot be quoted as compliant.",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
    if validation.status == ValidationStatus.UNKNOWN:
        raise _error(
            "QUOTATION_VALIDATION_UNKNOWN",
            "Product has unresolved technical requirements and cannot be quoted as compliant.",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    evidence_snapshot = None
    if embedder is not None:
        evidence = await get_product_evidence(
            session,
            product,
            request.requirements,
            embedder=embedder,
        )
        evidence_snapshot = evidence.model_dump(mode="json")

    pricing = product.pricing
    line_calc = calculate_line(
        request.quantity,
        pricing.unit_price,
        request.discount_percent,
    )
    totals = calculate_quotation([line_calc])

    quotation = Quotation(
        id=uuid.uuid4(),
        quotation_number=await _next_quotation_number(session),
        customer_name=request.customer_name,
        customer_email=str(request.customer_email) if request.customer_email else None,
        customer_reference=request.customer_reference,
        title=request.title,
        currency=pricing.currency,
        status=ModelQuotationStatus.DRAFT,
        validity_days=request.validity_days,
        lead_time_days=pricing.lead_time_days,
        technical_status=validation.status.value,
        subtotal=totals.subtotal,
        discount_percent=request.discount_percent,
        discount_amount=totals.discount_amount,
        total=totals.total,
        validation_snapshot=validation.model_dump(mode="json"),
        evidence_snapshot=evidence_snapshot,
    )
    session.add(quotation)
    await session.flush()

    session.add(
        QuotationLineItem(
            id=uuid.uuid4(),
            quotation_id=quotation.id,
            product_id=product.id,
            model_number=product.model_number,
            description=product.description or product.name,
            quantity=request.quantity,
            unit_price=pricing.unit_price,
            currency=pricing.currency,
            discount_percent=request.discount_percent,
            line_subtotal=line_calc.line_subtotal,
            line_total=line_calc.line_total,
        ),
    )
    await session.commit()
    return _quotation_to_response(await _load_quotation(session, quotation.id))


async def get_quotation(session: AsyncSession, quotation_id: UUID) -> QuotationResponse:
    return _quotation_to_response(await _load_quotation(session, quotation_id))


async def list_quotations(session: AsyncSession) -> QuotationListResponse:
    total = await session.scalar(select(func.count()).select_from(Quotation)) or 0
    result = await session.scalars(
        select(Quotation)
        .options(selectinload(Quotation.lines))
        .order_by(Quotation.created_at.desc()),
    )
    items = [_quotation_to_response(quotation) for quotation in result.all()]
    return QuotationListResponse(items=items, total=total)


async def update_quotation_status(
    session: AsyncSession,
    quotation_id: UUID,
    status_value: ModelQuotationStatus | str,
) -> QuotationResponse:
    quotation = await _load_quotation(session, quotation_id)
    quotation.status = ModelQuotationStatus(status_value)
    await session.commit()
    return _quotation_to_response(await _load_quotation(session, quotation.id))
