from uuid import UUID

from fastapi import APIRouter

from app.auth.deps import DbSession
from app.schemas.validation import (
    ProductValidationResult,
    ValidateProductRequest,
    ValidateProductsRequest,
    ValidateProductsResponse,
)
from app.services import validation as validation_service
from app.services.catalog import get_product_entity, get_products_by_ids

router = APIRouter(tags=["Validation"])


@router.post(
    "/validation/products/{product_id}",
    response_model=ProductValidationResult,
)
async def validate_product(
    session: DbSession,
    product_id: UUID,
    request: ValidateProductRequest,
) -> ProductValidationResult:
    product = await get_product_entity(session, product_id)
    return validation_service.validate_product(product, request.requirements)


@router.post("/validation/products", response_model=ValidateProductsResponse)
async def validate_products(
    session: DbSession,
    request: ValidateProductsRequest,
) -> ValidateProductsResponse:
    products = await get_products_by_ids(session, request.product_ids)
    results = validation_service.validate_products(products, request.requirements)
    return ValidateProductsResponse(results=results)
