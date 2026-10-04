"""RFQ extraction schemas for Phase 3 structured requirements."""

from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, WithJsonSchema, field_validator, model_validator

from app.domain.spec_keys import ALL_SPEC_KEYS, SpecKey

# Groq strict JSON Schema rejects overlapping integer/number unions. Use a single
# JSON Schema "number" while preserving Python int/float validation at runtime.
StructuredRequirementValue = Annotated[
    bool | int | float | str | list[str] | None,
    WithJsonSchema(
        {
            "anyOf": [
                {"type": "boolean"},
                {"type": "number"},
                {"type": "string"},
                {"items": {"type": "string"}, "type": "array"},
                {"type": "null"},
            ]
        }
    ),
]


class RequirementOperator(StrEnum):
    EQ = "eq"
    NEQ = "neq"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    CONTAINS = "contains"
    IN = "in"


class RequirementPriority(StrEnum):
    MUST_HAVE = "must_have"
    PREFERRED = "preferred"


# Groq strict JSON Schema rejects ambiguous anyOf($ref enum, null). Inline enum + null.
StructuredRequirementPriority = Annotated[
    RequirementPriority | None,
    WithJsonSchema(
        {
            "type": "string",
            "enum": ["must_have", "preferred", None],
        }
    ),
]


class StructuredRequirement(BaseModel):
    """Customer requirement extracted from RFQ text for Phase 4 validation."""

    model_config = ConfigDict(extra="forbid")

    spec_key: SpecKey
    operator: RequirementOperator
    # Required in JSON schema (nullable where applicable) for Groq strict structured outputs.
    value: StructuredRequirementValue = Field(...)
    unit: str | None = Field(...)
    required: bool = Field(...)
    priority: StructuredRequirementPriority = Field(...)
    source_text: str | None = Field(...)

    @model_validator(mode="before")
    @classmethod
    def apply_structured_requirement_defaults(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        defaults = {
            "value": None,
            "unit": None,
            "priority": None,
            "source_text": None,
            "required": True,
        }
        return {**defaults, **data}

    @field_validator("spec_key", mode="before")
    @classmethod
    def validate_spec_key(cls, value: str | SpecKey) -> SpecKey:
        key = SpecKey(value) if isinstance(value, str) else value
        if key.value not in ALL_SPEC_KEYS:
            raise ValueError(f"Unsupported specification key: {value}")
        return key


class AmbiguousRequirementNote(BaseModel):
    """RFQ language that could not be mapped to a concrete engineering specification."""

    model_config = ConfigDict(extra="forbid")

    source_text: str = Field(min_length=1)
    # Required in JSON schema (nullable) for Groq strict structured outputs.
    description: str | None = Field(
        ...,
        description="Explanation when RFQ language could not be mapped to a specification.",
    )


class RfqExtractRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    raw_text: str = Field(
        min_length=1,
        description="Customer RFQ text to extract requirements from.",
    )


class RfqExtractResponse(BaseModel):
    """Structured RFQ extraction result returned by the API."""

    model_config = ConfigDict(extra="forbid")

    customer_name: str | None = None
    customer_reference: str | None = None
    title: str | None = None
    quantity: int | None = Field(default=None, ge=1)
    requirements: list[StructuredRequirement] = Field(default_factory=list)
    ambiguous_notes: list[AmbiguousRequirementNote] = Field(default_factory=list)


class RfqExtractionResult(RfqExtractResponse):
    """Validated structured output model for Groq extraction."""

    # Required in JSON schema (nullable where applicable) for Groq strict structured outputs.
    customer_name: str | None = Field(...)
    customer_reference: str | None = Field(...)
    title: str | None = Field(...)
    quantity: int | None = Field(..., ge=1)
    requirements: list[StructuredRequirement] = Field(...)
    ambiguous_notes: list[AmbiguousRequirementNote] = Field(...)

    @model_validator(mode="before")
    @classmethod
    def apply_extraction_result_defaults(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        defaults = {
            "customer_name": None,
            "customer_reference": None,
            "title": None,
            "quantity": None,
            "requirements": [],
            "ambiguous_notes": [],
        }
        return {**defaults, **data}
