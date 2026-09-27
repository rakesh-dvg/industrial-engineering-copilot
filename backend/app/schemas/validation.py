"""Validation request/response schemas for Phase 4."""

from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.spec_keys import SpecKey
from app.schemas.rfq import RequirementOperator, RequirementPriority, StructuredRequirement


class ValidationStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


class RequirementValidationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    spec_key: SpecKey
    operator: RequirementOperator
    required: bool
    priority: RequirementPriority | None = None
    status: ValidationStatus
    required_value: bool | int | float | str | list[str] | None = None
    required_unit: str | None = None
    actual_value: bool | int | float | str | list[str] | None = None
    actual_unit: str | None = None
    details: str
    source_text: str | None = None


class ProductValidationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: UUID
    model_number: str
    status: ValidationStatus
    results: list[RequirementValidationResult]


class ValidateProductRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirements: list[StructuredRequirement] = Field(min_length=1)


class ValidateProductsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_ids: list[UUID] = Field(min_length=1)
    requirements: list[StructuredRequirement] = Field(min_length=1)


class ValidateProductsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    results: list[ProductValidationResult]
