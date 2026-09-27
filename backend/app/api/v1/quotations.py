from uuid import UUID

from fastapi import APIRouter

from app.auth.deps import DbSession
from app.embeddings.deps import get_embedding_provider
from app.schemas.quotation import (
    CreateQuotationRequest,
    QuotationListResponse,
    QuotationResponse,
    UpdateQuotationStatusRequest,
)
from app.services import quotations as quotation_service

router = APIRouter(tags=["Quotations"])


@router.post("/quotations", response_model=QuotationResponse)
async def create_quotation(
    session: DbSession,
    request: CreateQuotationRequest,
) -> QuotationResponse:
    return await quotation_service.create_quotation(
        session,
        request,
        embedder=get_embedding_provider(),
    )


@router.get("/quotations/{quotation_id}", response_model=QuotationResponse)
async def get_quotation(session: DbSession, quotation_id: UUID) -> QuotationResponse:
    return await quotation_service.get_quotation(session, quotation_id)


@router.get("/quotations", response_model=QuotationListResponse)
async def list_quotations(session: DbSession) -> QuotationListResponse:
    return await quotation_service.list_quotations(session)


@router.patch("/quotations/{quotation_id}/status", response_model=QuotationResponse)
async def update_quotation_status(
    session: DbSession,
    quotation_id: UUID,
    request: UpdateQuotationStatusRequest,
) -> QuotationResponse:
    return await quotation_service.update_quotation_status(
        session,
        quotation_id,
        request.status,
    )
