from uuid import UUID

from fastapi import APIRouter, Query

from app.auth.deps import DbSession
from app.schemas.catalog import (
    ManufacturerListResponse,
    ProductCategoryListResponse,
    ProductDetailResponse,
    ProductListResponse,
)
from app.services import catalog as catalog_service

router = APIRouter(tags=["Catalog"])


@router.get("/manufacturers", response_model=ManufacturerListResponse)
async def list_manufacturers(session: DbSession) -> ManufacturerListResponse:
    return await catalog_service.list_manufacturers(session)


@router.get("/product-categories", response_model=ProductCategoryListResponse)
async def list_product_categories(session: DbSession) -> ProductCategoryListResponse:
    return await catalog_service.list_product_categories(session)


@router.get("/products", response_model=ProductListResponse)
async def list_products(
    session: DbSession,
    category: str | None = Query(default=None, description="Category slug or name"),
    manufacturer: str | None = Query(default=None, description="Manufacturer name"),
    model_number: str | None = Query(default=None, description="Exact model number"),
    is_active: bool | None = Query(default=None),
) -> ProductListResponse:
    return await catalog_service.list_products(
        session,
        category=category,
        manufacturer=manufacturer,
        model_number=model_number,
        is_active=is_active,
    )


@router.get("/products/{product_id}", response_model=ProductDetailResponse)
async def get_product(session: DbSession, product_id: UUID) -> ProductDetailResponse:
    return await catalog_service.get_product(session, product_id)
