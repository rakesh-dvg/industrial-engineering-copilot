from uuid import UUID

from fastapi import APIRouter

from app.auth.deps import DbSession
from app.schemas.communication import (
    CreateQuotationCommunicationRequest,
    QuotationCommunicationResponse,
    SendQuotationResponse,
    UpdateQuotationCommunicationRequest,
)
from app.services import quotation_communication as communication_service

router = APIRouter(tags=["Quotations"])


@router.get(
    "/quotations/{quotation_id}/communication",
    response_model=QuotationCommunicationResponse | None,
)
async def get_quotation_communication(
    session: DbSession,
    quotation_id: UUID,
) -> QuotationCommunicationResponse | None:
    return await communication_service.get_quotation_communication(session, quotation_id)


@router.post(
    "/quotations/{quotation_id}/communication",
    response_model=QuotationCommunicationResponse,
)
async def create_quotation_communication(
    session: DbSession,
    quotation_id: UUID,
    request: CreateQuotationCommunicationRequest,
) -> QuotationCommunicationResponse:
    return await communication_service.create_quotation_communication(
        session,
        quotation_id,
        request,
    )


@router.patch(
    "/quotations/{quotation_id}/communication",
    response_model=QuotationCommunicationResponse,
)
async def update_quotation_communication(
    session: DbSession,
    quotation_id: UUID,
    request: UpdateQuotationCommunicationRequest,
) -> QuotationCommunicationResponse:
    return await communication_service.update_quotation_communication(
        session,
        quotation_id,
        request,
    )


@router.post(
    "/quotations/{quotation_id}/send",
    response_model=SendQuotationResponse,
)
async def send_quotation_to_customer(
    session: DbSession,
    quotation_id: UUID,
) -> SendQuotationResponse:
    return await communication_service.send_quotation_to_customer(session, quotation_id)
