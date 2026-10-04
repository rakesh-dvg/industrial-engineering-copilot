"""Quotation request/response schemas for Phase 7."""

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.rfq import StructuredRequirement
from app.schemas.validation import ValidationStatus


class QuotationStatus(StrEnum):
    DRAFT = "DRAFT"
    REVIEWED = "REVIEWED"
    APPROVED = "APPROVED"
    READY_TO_SEND = "READY_TO_SEND"
    SENT = "SENT"


class CreateQuotationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer_name: str = Field(min_length=1)
    customer_email: str | None = None
    customer_reference: str | None = None
    title: str | None = None
    product_id: UUID
    quantity: int = Field(ge=1)
    discount_percent: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    validity_days: int = Field(default=30, ge=1)
    requirements: list[StructuredRequirement] = Field(min_length=1)


class QuotationLineResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    product_id: UUID
    model_number: str
    description: str
    quantity: int
    unit_price: Decimal
    currency: str
    discount_percent: Decimal
    line_subtotal: Decimal
    line_total: Decimal


class QuotationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    quotation_number: str
    status: QuotationStatus
    customer_name: str
    customer_email: str | None = None
    customer_reference: str | None = None
    title: str | None = None
    currency: str
    validity_days: int
    lead_time_days: int
    technical_status: ValidationStatus
    subtotal: Decimal
    discount_percent: Decimal
    discount_amount: Decimal
    total: Decimal
    lines: list[QuotationLineResponse]
    validation_snapshot: dict
    evidence_snapshot: dict | None = None
    created_at: datetime
    updated_at: datetime


class QuotationListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[QuotationResponse]
    total: int


class UpdateQuotationStatusRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: QuotationStatus
