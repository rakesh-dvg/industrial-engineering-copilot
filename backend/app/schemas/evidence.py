"""Evidence schemas for Phase 6 datasheet RAG."""

from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.spec_keys import SpecKey
from app.schemas.rfq import RequirementOperator, RequirementPriority, StructuredRequirement
from app.schemas.validation import ValidationStatus


class EvidenceStatus(StrEnum):
    FOUND = "found"
    NOT_FOUND = "not_found"
    INSUFFICIENT = "insufficient"


class EvidenceItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    page_number: int | None = None
    document_id: UUID
    chunk_id: UUID
    document_title: str
    document_filename: str
    similarity_score: float = Field(ge=0.0, le=1.0)


class RequirementEvidenceResult(BaseModel):
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
    evidence_status: EvidenceStatus
    evidence: list[EvidenceItem] = Field(default_factory=list)


class ProductEvidenceResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: UUID
    model_number: str
    status: ValidationStatus
    requirements: list[RequirementEvidenceResult]


class ProductEvidenceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirements: list[StructuredRequirement] = Field(min_length=1)


class ProductsEvidenceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_ids: list[UUID] = Field(min_length=1)
    requirements: list[StructuredRequirement] = Field(min_length=1)


class ProductsEvidenceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    results: list[ProductEvidenceResult]


class DocumentIngestResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: UUID
    product_id: UUID
    title: str
    filename: str
    mime_type: str
    page_count: int | None
    ingest_status: str
    chunk_count: int
