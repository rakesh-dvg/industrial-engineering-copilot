from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ManufacturerSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None = None
    website: str | None = None
    is_active: bool


class ProductCategorySummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    description: str | None = None
    is_active: bool


class ProductSpecificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    spec_key: str
    numeric_value: Decimal | None = None
    text_value: str | None = None
    boolean_value: bool | None = None
    unit: str | None = None
    source: str | None = None


class ProductPricingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    unit_price: Decimal
    currency: str
    discount_percent: Decimal
    lead_time_days: int
    price_valid_until: date | None = None
    is_active: bool


class ProductListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    model_number: str
    name: str
    description: str | None = None
    is_active: bool
    manufacturer: ManufacturerSummary
    category: ProductCategorySummary
    pricing: ProductPricingResponse | None = None


class ProductDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    model_number: str
    name: str
    description: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    manufacturer: ManufacturerSummary
    category: ProductCategorySummary
    specifications: list[ProductSpecificationResponse] = Field(default_factory=list)
    pricing: ProductPricingResponse | None = None


class ManufacturerListResponse(BaseModel):
    items: list[ManufacturerSummary]


class ProductCategoryListResponse(BaseModel):
    items: list[ProductCategorySummary]


class ProductListResponse(BaseModel):
    items: list[ProductListItem]
    total: int
