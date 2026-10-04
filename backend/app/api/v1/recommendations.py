from fastapi import APIRouter, HTTPException, status

from app.auth.deps import DbSession
from app.embeddings.deps import get_embedding_provider
from app.schemas.errors import ErrorDetail, ErrorResponse
from app.schemas.recommendation import RecommendationResult, RecommendProductsRequest
from app.services.catalog import get_products_by_ids
from app.services.recommendation import recommend_products

router = APIRouter(tags=["Recommendations"])


@router.post("/recommendations/products", response_model=RecommendationResult)
async def recommend_products_endpoint(
    session: DbSession,
    request: RecommendProductsRequest,
) -> RecommendationResult:
    if not request.product_ids:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=ErrorResponse(
                error=ErrorDetail(
                    code="NO_RECOMMENDATION_CANDIDATES",
                    message="No candidate products were provided for recommendation.",
                ),
            ).model_dump(),
        )

    products = await get_products_by_ids(session, request.product_ids)
    return await recommend_products(
        session,
        products,
        request.requirements,
        embedder=get_embedding_provider(),
    )
