from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.manufacturer import Manufacturer
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.schemas.catalog import (
    ManufacturerListResponse,
    ManufacturerSummary,
    ProductCategoryListResponse,
    ProductCategorySummary,
    ProductDetailResponse,
    ProductListItem,
    ProductListResponse,
)
from app.schemas.errors import ErrorDetail, ErrorResponse


def _not_found(message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=ErrorResponse(
            error=ErrorDetail(code="NOT_FOUND", message=message),
        ).model_dump(),
    )


def _product_load_options():
    return (
        selectinload(Product.manufacturer),
        selectinload(Product.category),
        selectinload(Product.specifications),
        selectinload(Product.pricing),
    )


async def list_manufacturers(session: AsyncSession) -> ManufacturerListResponse:
    result = await session.scalars(
        select(Manufacturer).order_by(Manufacturer.name),
    )
    items = [ManufacturerSummary.model_validate(row) for row in result.all()]
    return ManufacturerListResponse(items=items)


async def list_product_categories(session: AsyncSession) -> ProductCategoryListResponse:
    result = await session.scalars(
        select(ProductCategory).order_by(ProductCategory.name),
    )
    items = [ProductCategorySummary.model_validate(row) for row in result.all()]
    return ProductCategoryListResponse(items=items)


async def list_products(
    session: AsyncSession,
    *,
    category: str | None = None,
    manufacturer: str | None = None,
    model_number: str | None = None,
    is_active: bool | None = None,
) -> ProductListResponse:
    query = select(Product).options(*_product_load_options())

    if category is not None:
        query = query.join(Product.category).where(
            (ProductCategory.slug == category) | (ProductCategory.name == category),
        )
    if manufacturer is not None:
        query = query.join(Product.manufacturer).where(Manufacturer.name == manufacturer)
    if model_number is not None:
        query = query.where(Product.model_number == model_number)
    if is_active is not None:
        query = query.where(Product.is_active.is_(is_active))

    count_query = select(func.count()).select_from(query.subquery())
    total = await session.scalar(count_query) or 0

    result = await session.scalars(query.order_by(Product.model_number))
    items = [ProductListItem.model_validate(row) for row in result.all()]
    return ProductListResponse(items=items, total=total)


async def get_product(session: AsyncSession, product_id: UUID) -> ProductDetailResponse:
    product = await get_product_entity(session, product_id)
    return ProductDetailResponse.model_validate(product)


async def get_product_entity(session: AsyncSession, product_id: UUID) -> Product:
    product = await session.scalar(
        select(Product)
        .options(*_product_load_options())
        .where(Product.id == product_id),
    )
    if product is None:
        raise _not_found("Product not found.")
    return product


async def get_products_by_ids(session: AsyncSession, product_ids: list[UUID]) -> list[Product]:
    if not product_ids:
        return []
    result = await session.scalars(
        select(Product)
        .options(*_product_load_options())
        .where(Product.id.in_(product_ids)),
    )
    products_by_id = {product.id: product for product in result.all()}
    missing = [str(product_id) for product_id in product_ids if product_id not in products_by_id]
    if missing:
        raise _not_found(f"Product not found: {', '.join(missing)}.")
    return [products_by_id[product_id] for product_id in product_ids]
