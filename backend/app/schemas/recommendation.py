"""Product recommendation schemas for Phase 5A."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.rfq import StructuredRequirement
from app.schemas.validation import ValidationStatus


class EvidenceCoverage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    supported: int = Field(ge=0)
    required: int = Field(ge=0)


class RecommendationItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: UUID
    model_number: str
    manufacturer_name: str
    product_name: str
    validation_status: ValidationStatus
    recommendation_score: int = Field(ge=0, le=100)
    evidence_coverage: EvidenceCoverage
    unit_price: str | None = None
    currency: str | None = None
    lead_time_days: int | None = None
    reasons: list[str] = Field(default_factory=list)


class ExcludedProduct(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: UUID
    model_number: str
    validation_status: ValidationStatus
    reason: str


class RecommendProductsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_ids: list[UUID] = Field(default_factory=list)
    requirements: list[StructuredRequirement] = Field(min_length=1)


class RecommendationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirements_summary: str
    candidate_count: int = Field(ge=0)
    eligible_count: int = Field(ge=0)
    primary_recommendation: RecommendationItem | None = None
    alternatives: list[RecommendationItem] = Field(default_factory=list)
    excluded_products: list[ExcludedProduct] = Field(default_factory=list)
    message: str | None = None
