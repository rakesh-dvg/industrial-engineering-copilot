"""Sales follow-up schemas for Phase 8.5."""

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class FollowUpPriority(StrEnum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"


class FollowUpStatus(StrEnum):
    OPEN = "OPEN"
    COMPLETED = "COMPLETED"


class FollowUpQuotationSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    quotation_number: str
    status: str
    currency: str
    total: Decimal
    sent_at: datetime | None = None


class SalesFollowUpResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    quotation_id: UUID
    customer_name: str
    customer_email: str
    quotation_number: str
    follow_up_date: date
    priority: FollowUpPriority
    status: FollowUpStatus
    notes: str | None = None
    quotation: FollowUpQuotationSummary
    created_at: datetime
    updated_at: datetime


class SalesFollowUpListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[SalesFollowUpResponse]
    total: int


class UpdateSalesFollowUpRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    follow_up_date: date | None = None
    priority: FollowUpPriority | None = None
    status: FollowUpStatus | None = None
    notes: str | None = None
