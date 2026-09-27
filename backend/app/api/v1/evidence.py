from uuid import UUID

from fastapi import APIRouter

from app.auth.deps import DbSession
from app.embeddings.deps import get_embedding_provider
from app.schemas.evidence import (
    ProductEvidenceRequest,
    ProductEvidenceResult,
    ProductsEvidenceRequest,
    ProductsEvidenceResponse,
)
from app.services.catalog import get_product_entity, get_products_by_ids
from app.services.evidence import get_product_evidence

router = APIRouter(tags=["Evidence"])


@router.post(
    "/evidence/products/{product_id}",
    response_model=ProductEvidenceResult,
)
async def get_product_evidence_endpoint(
    session: DbSession,
    product_id: UUID,
    request: ProductEvidenceRequest,
) -> ProductEvidenceResult:
    product = await get_product_entity(session, product_id)
    return await get_product_evidence(
        session,
        product,
        request.requirements,
        embedder=get_embedding_provider(),
    )


@router.post("/evidence/products", response_model=ProductsEvidenceResponse)
async def get_products_evidence_endpoint(
    session: DbSession,
    request: ProductsEvidenceRequest,
) -> ProductsEvidenceResponse:
    products = await get_products_by_ids(session, request.product_ids)
    results = []
    embedder = get_embedding_provider()
    for product in products:
        results.append(
            await get_product_evidence(
                session,
                product,
                request.requirements,
                embedder=embedder,
            ),
        )
    return ProductsEvidenceResponse(results=results)
