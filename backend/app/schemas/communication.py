"""Quotation communication schemas for Phase 8.5."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CommunicationStatus(StrEnum):
    DRAFT = "DRAFT"
    READY_TO_SEND = "READY_TO_SEND"
    SENT = "SENT"


class QuotationCommunicationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    quotation_id: UUID
    customer_name: str
    customer_email: str
    subject: str
    body: str
    status: CommunicationStatus
    sent_at: datetime | None = None
    demo_mode: bool = True
    created_at: datetime
    updated_at: datetime


class CreateQuotationCommunicationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer_email: str | None = None


class UpdateQuotationCommunicationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer_email: str | None = None
    subject: str | None = Field(default=None, min_length=1, max_length=255)
    body: str | None = Field(default=None, min_length=1)
    status: CommunicationStatus | None = None


class SendQuotationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quotation_id: UUID
    communication: QuotationCommunicationResponse
    send_detail: str
    demo_mode: bool = True
