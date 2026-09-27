"""Sales follow-up queue for sent quotations."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.quotation import Quotation, QuotationStatus
from app.models.sales_follow_up import FollowUpPriority, FollowUpStatus, SalesFollowUp
from app.schemas.errors import ErrorDetail, ErrorResponse
from app.schemas.followup import (
    FollowUpPriority as SchemaFollowUpPriority,
)
from app.schemas.followup import (
    FollowUpQuotationSummary,
    SalesFollowUpListResponse,
    SalesFollowUpResponse,
    UpdateSalesFollowUpRequest,
)
from app.schemas.followup import (
    FollowUpStatus as SchemaFollowUpStatus,
)


def _error(code: str, message: str, status_code: int) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail=ErrorResponse(error=ErrorDetail(code=code, message=message)).model_dump(),
    )


def follow_up_to_response(follow_up: SalesFollowUp) -> SalesFollowUpResponse:
    quotation = follow_up.quotation
    sent_at = quotation.communication.sent_at if quotation.communication else None
    return SalesFollowUpResponse(
        id=follow_up.id,
        quotation_id=follow_up.quotation_id,
        customer_name=follow_up.customer_name,
        customer_email=follow_up.customer_email,
        quotation_number=follow_up.quotation_number,
        follow_up_date=follow_up.follow_up_date,
        priority=SchemaFollowUpPriority(str(follow_up.priority)),
        status=SchemaFollowUpStatus(str(follow_up.status)),
        notes=follow_up.notes,
        quotation=FollowUpQuotationSummary(
            id=quotation.id,
            quotation_number=quotation.quotation_number,
            status=str(quotation.status),
            currency=quotation.currency,
            total=quotation.total,
            sent_at=sent_at,
        ),
        created_at=follow_up.created_at,
        updated_at=follow_up.updated_at,
    )


async def list_follow_ups(
    session: AsyncSession,
    *,
    status_filter: FollowUpStatus | None = None,
    due_date: date | None = None,
    sent_only: bool = False,
) -> SalesFollowUpListResponse:
    query = (
        select(SalesFollowUp)
        .options(
            selectinload(SalesFollowUp.quotation).selectinload(Quotation.communication),
        )
        .order_by(SalesFollowUp.follow_up_date.asc(), SalesFollowUp.priority.asc())
    )

    if status_filter is not None:
        query = query.where(SalesFollowUp.status == status_filter)
    if due_date is not None:
        query = query.where(SalesFollowUp.follow_up_date == due_date)
    if sent_only:
        query = query.join(SalesFollowUp.quotation).where(
            Quotation.status == QuotationStatus.SENT,
        )

    count_query = select(func.count()).select_from(query.subquery())
    total = await session.scalar(count_query) or 0
    result = await session.scalars(query)
    items = [follow_up_to_response(item) for item in result.all()]
    return SalesFollowUpListResponse(items=items, total=total)


async def update_follow_up(
    session: AsyncSession,
    follow_up_id: UUID,
    request: UpdateSalesFollowUpRequest,
) -> SalesFollowUpResponse:
    follow_up = await session.scalar(
        select(SalesFollowUp)
        .options(
            selectinload(SalesFollowUp.quotation).selectinload(Quotation.communication),
        )
        .where(SalesFollowUp.id == follow_up_id),
    )
    if follow_up is None:
        raise _error("NOT_FOUND", "Follow-up not found.", status.HTTP_404_NOT_FOUND)

    if request.follow_up_date is not None:
        follow_up.follow_up_date = request.follow_up_date
    if request.priority is not None:
        follow_up.priority = FollowUpPriority(request.priority.value)
    if request.status is not None:
        follow_up.status = FollowUpStatus(request.status.value)
    if request.notes is not None:
        follow_up.notes = request.notes

    await session.commit()
    await session.refresh(follow_up)
    return follow_up_to_response(follow_up)
