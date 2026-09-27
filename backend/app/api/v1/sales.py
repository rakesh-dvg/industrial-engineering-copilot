from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.auth.deps import DbSession
from app.models.sales_follow_up import FollowUpStatus
from app.schemas.followup import (
    SalesFollowUpListResponse,
    SalesFollowUpResponse,
    UpdateSalesFollowUpRequest,
)
from app.services import sales_followups as follow_up_service

router = APIRouter(tags=["Sales"])


@router.get("/sales/follow-ups", response_model=SalesFollowUpListResponse)
async def list_sales_follow_ups(
    session: DbSession,
    status: Annotated[FollowUpStatus | None, Query()] = None,
    due_date: Annotated[date | None, Query()] = None,
    sent_only: Annotated[bool, Query()] = False,
) -> SalesFollowUpListResponse:
    return await follow_up_service.list_follow_ups(
        session,
        status_filter=status,
        due_date=due_date,
        sent_only=sent_only,
    )


@router.patch("/sales/follow-ups/{follow_up_id}", response_model=SalesFollowUpResponse)
async def update_sales_follow_up(
    session: DbSession,
    follow_up_id: UUID,
    request: UpdateSalesFollowUpRequest,
) -> SalesFollowUpResponse:
    return await follow_up_service.update_follow_up(session, follow_up_id, request)
