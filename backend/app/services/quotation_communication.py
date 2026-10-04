"""Quotation customer communication and send workflow."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.email.base import EmailMessage, EmailSender
from app.email.demo_sender import get_email_sender
from app.models.quotation import Quotation
from app.models.quotation import QuotationStatus as ModelQuotationStatus
from app.models.quotation_communication import CommunicationStatus, QuotationCommunication
from app.models.sales_follow_up import FollowUpPriority, FollowUpStatus, SalesFollowUp
from app.schemas.communication import (
    CommunicationStatus as SchemaCommunicationStatus,
)
from app.schemas.communication import (
    CreateQuotationCommunicationRequest,
    QuotationCommunicationResponse,
    SendQuotationResponse,
    UpdateQuotationCommunicationRequest,
)
from app.schemas.errors import ErrorDetail, ErrorResponse
from app.schemas.validation import ValidationStatus
from app.services.quotation_email import build_email_body, build_email_subject


def _error(code: str, message: str, status_code: int) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail=ErrorResponse(error=ErrorDetail(code=code, message=message)).model_dump(),
    )


def _communication_to_response(
    communication: QuotationCommunication,
) -> QuotationCommunicationResponse:
    return QuotationCommunicationResponse(
        id=communication.id,
        quotation_id=communication.quotation_id,
        customer_name=communication.customer_name,
        customer_email=communication.customer_email,
        subject=communication.subject,
        body=communication.body,
        status=SchemaCommunicationStatus(str(communication.status)),
        sent_at=communication.sent_at,
        demo_mode=True,
        created_at=communication.created_at,
        updated_at=communication.updated_at,
    )


async def _load_quotation(session: AsyncSession, quotation_id: UUID) -> Quotation:
    quotation = await session.scalar(
        select(Quotation)
        .options(
            selectinload(Quotation.lines),
            selectinload(Quotation.communication),
            selectinload(Quotation.follow_up),
        )
        .where(Quotation.id == quotation_id),
    )
    if quotation is None:
        raise _error("NOT_FOUND", "Quotation not found.", status.HTTP_404_NOT_FOUND)
    return quotation


def _default_customer_email(quotation: Quotation) -> str:
    if quotation.customer_email:
        return quotation.customer_email
    slug = quotation.customer_name.lower().replace(" ", "")
    return f"procurement@{slug}.example"


async def get_quotation_communication(
    session: AsyncSession,
    quotation_id: UUID,
) -> QuotationCommunicationResponse | None:
    quotation = await _load_quotation(session, quotation_id)
    if quotation.communication is None:
        return None
    return _communication_to_response(quotation.communication)


async def create_quotation_communication(
    session: AsyncSession,
    quotation_id: UUID,
    request: CreateQuotationCommunicationRequest,
) -> QuotationCommunicationResponse:
    quotation = await _load_quotation(session, quotation_id)

    if quotation.status not in {
        ModelQuotationStatus.APPROVED,
        ModelQuotationStatus.READY_TO_SEND,
        ModelQuotationStatus.SENT,
    }:
        raise _error(
            "QUOTATION_NOT_APPROVED",
            "Customer communication can only be prepared for approved quotations.",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    if quotation.technical_status != ValidationStatus.PASS.value:
        raise _error(
            "QUOTATION_NOT_COMPLIANT",
            "Only technically compliant quotations can be communicated to customers.",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    if quotation.communication is not None:
        return _communication_to_response(quotation.communication)

    customer_email = request.customer_email or _default_customer_email(quotation)
    quotation.customer_email = str(customer_email)

    communication = QuotationCommunication(
        id=uuid.uuid4(),
        quotation_id=quotation.id,
        customer_name=quotation.customer_name,
        customer_email=str(customer_email),
        subject=build_email_subject(quotation),
        body=build_email_body(quotation),
        status=CommunicationStatus.DRAFT,
    )
    session.add(communication)
    await session.commit()
    await session.refresh(communication)
    return _communication_to_response(communication)


async def update_quotation_communication(
    session: AsyncSession,
    quotation_id: UUID,
    request: UpdateQuotationCommunicationRequest,
) -> QuotationCommunicationResponse:
    quotation = await _load_quotation(session, quotation_id)
    if quotation.communication is None:
        raise _error(
            "COMMUNICATION_NOT_FOUND",
            "Quotation communication draft was not found.",
            status.HTTP_404_NOT_FOUND,
        )

    communication = quotation.communication
    if communication.status == CommunicationStatus.SENT:
        raise _error(
            "COMMUNICATION_ALREADY_SENT",
            "Sent quotation communication cannot be modified.",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    if request.customer_email is not None:
        communication.customer_email = str(request.customer_email)
        quotation.customer_email = str(request.customer_email)
    if request.subject is not None:
        communication.subject = request.subject
    if request.body is not None:
        communication.body = request.body
    if request.status is not None:
        communication.status = CommunicationStatus(request.status.value)
        if communication.status == CommunicationStatus.READY_TO_SEND:
            quotation.status = ModelQuotationStatus.READY_TO_SEND

    await session.commit()
    await session.refresh(communication)
    return _communication_to_response(communication)


async def send_quotation_to_customer(
    session: AsyncSession,
    quotation_id: UUID,
    *,
    email_sender: EmailSender | None = None,
) -> SendQuotationResponse:
    quotation = await _load_quotation(session, quotation_id)

    if quotation.technical_status != ValidationStatus.PASS.value:
        raise _error(
            "QUOTATION_NOT_COMPLIANT",
            "Only technically compliant quotations can be sent to customers.",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    if quotation.status == ModelQuotationStatus.SENT:
        raise _error(
            "QUOTATION_ALREADY_SENT",
            "This quotation has already been sent to the customer.",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    if quotation.status not in {
        ModelQuotationStatus.APPROVED,
        ModelQuotationStatus.READY_TO_SEND,
    }:
        raise _error(
            "QUOTATION_NOT_APPROVED",
            "Quotation must be approved before it can be sent to the customer.",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    if quotation.communication is None:
        raise _error(
            "COMMUNICATION_NOT_FOUND",
            "Save a customer communication draft before sending.",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    communication = quotation.communication
    if communication.status == CommunicationStatus.SENT:
        raise _error(
            "QUOTATION_ALREADY_SENT",
            "This quotation has already been sent to the customer.",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    if not communication.customer_email:
        raise _error(
            "CUSTOMER_EMAIL_REQUIRED",
            "Customer email is required before sending the quotation.",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    sender = email_sender or get_email_sender()
    send_result = await sender.send(
        EmailMessage(
            recipient=communication.customer_email,
            subject=communication.subject,
            body=communication.body,
            attachment_name=f"{quotation.quotation_number}.pdf",
        ),
    )

    sent_at = datetime.now(tz=UTC)
    communication.status = CommunicationStatus.SENT
    communication.sent_at = sent_at
    quotation.status = ModelQuotationStatus.SENT
    quotation.customer_email = communication.customer_email

    if quotation.follow_up is None:
        follow_up = SalesFollowUp(
            id=uuid.uuid4(),
            quotation_id=quotation.id,
            customer_name=quotation.customer_name,
            customer_email=communication.customer_email,
            quotation_number=quotation.quotation_number,
            follow_up_date=sent_at.date(),
            priority=FollowUpPriority.P1,
            status=FollowUpStatus.OPEN,
        )
        session.add(follow_up)

    await session.commit()
    await session.refresh(communication)

    return SendQuotationResponse(
        quotation_id=quotation.id,
        communication=_communication_to_response(communication),
        send_detail=send_result.detail,
        demo_mode=not send_result.delivered,
    )


async def list_sent_quotation_communications(
    session: AsyncSession,
) -> list[QuotationCommunicationResponse]:
    result = await session.scalars(
        select(QuotationCommunication)
        .where(QuotationCommunication.status == CommunicationStatus.SENT)
        .order_by(QuotationCommunication.sent_at.desc()),
    )
    return [_communication_to_response(item) for item in result.all()]
