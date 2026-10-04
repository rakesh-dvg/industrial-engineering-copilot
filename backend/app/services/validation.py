"""Deterministic engineering validation (Phase 4)."""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Literal

from app.domain.spec_keys import SpecKey
from app.domain.units import normalize_numeric
from app.models.product import Product
from app.models.product_specification import ProductSpecification
from app.schemas.rfq import RequirementOperator, RequirementPriority, StructuredRequirement
from app.schemas.validation import (
    ProductValidationResult,
    RequirementValidationResult,
    ValidationStatus,
)

BOOLEAN_SPEC_KEYS = frozenset(
    {
        SpecKey.DIN_RAIL_MOUNTABLE,
        SpecKey.SUPPORTS_MODBUS_TCP,
    },
)

def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def spec_label(spec_key: SpecKey) -> str:
    return spec_key.value.replace("_", " ")


def is_must_have(requirement: StructuredRequirement) -> bool:
    if requirement.priority == RequirementPriority.PREFERRED:
        return False
    if requirement.priority == RequirementPriority.MUST_HAVE:
        return True
    return requirement.required


def build_spec_lookup(
    specifications: list[ProductSpecification],
) -> dict[str, ProductSpecification]:
    lookup: dict[str, ProductSpecification] = {}
    for spec in specifications:
        lookup.setdefault(spec.spec_key, spec)
    return lookup


def _decimal_to_number(value: Decimal) -> int | float:
    normalized = float(value)
    if normalized.is_integer():
        return int(normalized)
    return normalized


def _format_number(value: int | float) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _format_with_unit(value: int | float, unit: str | None) -> str:
    if unit:
        return f"{_format_number(value)} {unit}"
    return _format_number(value)


def _spec_missing_message(spec_key: SpecKey) -> str:
    return f"Product does not contain {spec_key.value}."


def _actual_from_spec(
    spec: ProductSpecification | None,
) -> tuple[
    Literal["missing", "boolean", "numeric", "text"],
    bool | int | float | str | None,
    str | None,
]:
    if spec is None:
        return "missing", None, None
    if spec.boolean_value is not None:
        return "boolean", spec.boolean_value, None
    if spec.numeric_value is not None:
        return "numeric", _decimal_to_number(spec.numeric_value), spec.unit
    if spec.text_value is not None:
        return "text", spec.text_value, None
    return "missing", None, None


def _evaluate_boolean_eq(
    requirement: StructuredRequirement,
    actual: bool,
) -> tuple[ValidationStatus, str]:
    required = requirement.value
    if not isinstance(required, bool):
        return (
            ValidationStatus.UNKNOWN,
            f"Requirement value is incompatible with boolean {spec_label(requirement.spec_key)}.",
        )
    if actual == required:
        return (
            ValidationStatus.PASS,
            f"Product has {str(actual).lower()} for {spec_label(requirement.spec_key)}; "
            f"requirement is {str(required).lower()}.",
        )
    return (
        ValidationStatus.FAIL,
        f"Product has {str(actual).lower()} for {spec_label(requirement.spec_key)}; "
        f"requirement is {str(required).lower()}.",
    )


def _evaluate_numeric(
    requirement: StructuredRequirement,
    actual_value: int | float,
    actual_unit: str | None,
) -> tuple[ValidationStatus, str]:
    required_raw = requirement.value
    if not isinstance(required_raw, (int, float)):
        return (
            ValidationStatus.UNKNOWN,
            f"Requirement value is incompatible with numeric {spec_label(requirement.spec_key)}.",
        )

    required_norm = normalize_numeric(
        float(required_raw),
        requirement.unit,
        requirement.spec_key.value,
    )
    actual_norm = normalize_numeric(
        float(actual_value),
        actual_unit,
        requirement.spec_key.value,
    )

    if required_norm is None:
        return (
            ValidationStatus.UNKNOWN,
            f"Requirement unit is incompatible with {spec_label(requirement.spec_key)}.",
        )
    if actual_norm is None:
        return (
            ValidationStatus.UNKNOWN,
            (
                f"Product {spec_label(requirement.spec_key)} value "
                "cannot be normalized for comparison."
            ),
        )

    operator = requirement.operator
    passed = _compare_numeric(operator, actual_norm, required_norm)
    status = ValidationStatus.PASS if passed else ValidationStatus.FAIL
    details = _numeric_details(
        requirement.spec_key,
        operator,
        actual_value,
        actual_unit,
        required_raw,
        requirement.unit,
        status,
    )
    return status, details


def _compare_numeric(
    operator: RequirementOperator,
    actual: float,
    required: float,
) -> bool:
    if operator == RequirementOperator.EQ:
        return actual == required
    if operator == RequirementOperator.NEQ:
        return actual != required
    if operator == RequirementOperator.GT:
        return actual > required
    if operator == RequirementOperator.GTE:
        return actual >= required
    if operator == RequirementOperator.LT:
        return actual < required
    if operator == RequirementOperator.LTE:
        return actual <= required
    return False


def _operator_phrase(operator: RequirementOperator, required: int | float) -> str:
    required_text = _format_number(required)
    mapping = {
        RequirementOperator.EQ: f"equals {required_text}",
        RequirementOperator.NEQ: f"does not equal {required_text}",
        RequirementOperator.GT: f"greater than {required_text}",
        RequirementOperator.GTE: f"at least {required_text}",
        RequirementOperator.LT: f"less than {required_text}",
        RequirementOperator.LTE: f"at most {required_text}",
    }
    return mapping[operator]


def _numeric_details(
    spec_key: SpecKey,
    operator: RequirementOperator,
    actual_value: int | float,
    actual_unit: str | None,
    required_value: int | float,
    required_unit: str | None,
    status: ValidationStatus,
) -> str:
    label = spec_label(spec_key)
    actual_text = _format_with_unit(actual_value, actual_unit)
    required_text = (
        _format_with_unit(required_value, required_unit)
        if required_unit
        else _format_number(required_value)
    )
    if operator == RequirementOperator.EQ:
        return f"Product has {actual_text} {label}; requirement is {required_text}."
    if operator == RequirementOperator.NEQ:
        relation = "is not" if status == ValidationStatus.PASS else "is"
        return f"Product has {actual_text} {label}; requirement {relation} {required_text}."

    phrase = _operator_phrase(operator, required_value)
    return f"Product has {actual_text} {label}; requirement is {phrase}."


def _evaluate_text_neq(
    requirement: StructuredRequirement,
    actual_text: str,
) -> tuple[ValidationStatus, str]:
    required = requirement.value
    if not isinstance(required, str):
        return (
            ValidationStatus.UNKNOWN,
            f"Requirement value is incompatible with text {spec_label(requirement.spec_key)}.",
        )
    if normalize_text(actual_text) != normalize_text(required):
        return (
            ValidationStatus.PASS,
            f"Product has \"{actual_text}\" for {spec_label(requirement.spec_key)}; "
            f"requirement is not \"{required}\".",
        )
    return (
        ValidationStatus.FAIL,
        f"Product has \"{actual_text}\" for {spec_label(requirement.spec_key)}; "
        f"requirement is not \"{required}\".",
    )


def _evaluate_text_eq(
    requirement: StructuredRequirement,
    actual_text: str,
) -> tuple[ValidationStatus, str]:
    required = requirement.value
    if not isinstance(required, str):
        return (
            ValidationStatus.UNKNOWN,
            f"Requirement value is incompatible with text {spec_label(requirement.spec_key)}.",
        )
    if normalize_text(actual_text) == normalize_text(required):
        return (
            ValidationStatus.PASS,
            f"Product has \"{actual_text}\" for {spec_label(requirement.spec_key)}; "
            f"requirement is \"{required}\".",
        )
    return (
        ValidationStatus.FAIL,
        f"Product has \"{actual_text}\" for {spec_label(requirement.spec_key)}; "
        f"requirement is \"{required}\".",
    )


def _evaluate_contains(
    requirement: StructuredRequirement,
    actual_text: str,
) -> tuple[ValidationStatus, str]:
    required = requirement.value
    if not isinstance(required, str):
        return (
            ValidationStatus.UNKNOWN,
            (
                "Requirement value is incompatible with contains on "
                f"{spec_label(requirement.spec_key)}."
            ),
        )
    normalized_actual = normalize_text(actual_text)
    normalized_required = normalize_text(required)
    if normalized_required in normalized_actual:
        return (
            ValidationStatus.PASS,
            f"Product value \"{actual_text}\" contains \"{required}\".",
        )
    return (
        ValidationStatus.FAIL,
        f"Product value \"{actual_text}\" does not contain \"{required}\".",
    )


def _evaluate_in(
    requirement: StructuredRequirement,
    actual_text: str,
) -> tuple[ValidationStatus, str]:
    required = requirement.value
    if not isinstance(required, list) or not all(isinstance(item, str) for item in required):
        return (
            ValidationStatus.UNKNOWN,
            (
                "Requirement value is incompatible with in operator on "
                f"{spec_label(requirement.spec_key)}."
            ),
        )
    allowed = {normalize_text(item) for item in required}
    normalized_actual = normalize_text(actual_text)
    if normalized_actual in allowed:
        return (
            ValidationStatus.PASS,
            f"Product value \"{actual_text}\" is in {required}.",
        )
    return (
        ValidationStatus.FAIL,
        f"Product value \"{actual_text}\" is not in {required}.",
    )


def evaluate_requirement(
    requirement: StructuredRequirement,
    spec: ProductSpecification | None,
) -> RequirementValidationResult:
    kind, actual_value, actual_unit = _actual_from_spec(spec)

    base = RequirementValidationResult(
        spec_key=requirement.spec_key,
        operator=requirement.operator,
        required=requirement.required,
        priority=requirement.priority,
        status=ValidationStatus.UNKNOWN,
        required_value=requirement.value,
        required_unit=requirement.unit,
        actual_value=actual_value,
        actual_unit=actual_unit,
        details="",
        source_text=requirement.source_text,
    )

    if kind == "missing":
        base.details = _spec_missing_message(requirement.spec_key)
        return base

    operator = requirement.operator
    spec_key = requirement.spec_key

    if spec_key in BOOLEAN_SPEC_KEYS:
        if operator != RequirementOperator.EQ:
            base.details = (
                f"Operator {operator.value} is not supported for boolean {spec_label(spec_key)}."
            )
            return base
        if kind != "boolean":
            base.details = f"Product {spec_label(spec_key)} is not a boolean value."
            return base
        status, details = _evaluate_boolean_eq(requirement, actual_value)  # type: ignore[arg-type]
        base.status = status
        base.details = details
        return base

    if operator in {
        RequirementOperator.GT,
        RequirementOperator.GTE,
        RequirementOperator.LT,
        RequirementOperator.LTE,
        RequirementOperator.EQ,
        RequirementOperator.NEQ,
    }:
        if kind == "numeric":
            status, details = _evaluate_numeric(requirement, actual_value, actual_unit)  # type: ignore[arg-type]
            base.status = status
            base.details = details
            return base
        if kind == "text" and operator in {RequirementOperator.EQ, RequirementOperator.NEQ}:
            if operator == RequirementOperator.EQ:
                status, details = _evaluate_text_eq(requirement, actual_value)  # type: ignore[arg-type]
            else:
                status, details = _evaluate_text_neq(requirement, actual_value)  # type: ignore[arg-type]
            base.status = status
            base.details = details
            return base
        base.details = f"Product {spec_label(spec_key)} value cannot be interpreted as numeric."
        return base

    if operator == RequirementOperator.CONTAINS:
        if kind != "text":
            base.details = f"Product {spec_label(spec_key)} is not a text value."
            return base
        status, details = _evaluate_contains(requirement, actual_value)  # type: ignore[arg-type]
        base.status = status
        base.details = details
        return base

    if operator == RequirementOperator.IN:
        if kind != "text":
            base.details = f"Product {spec_label(spec_key)} is not a text value."
            return base
        status, details = _evaluate_in(requirement, actual_value)  # type: ignore[arg-type]
        base.status = status
        base.details = details
        return base

    base.details = f"Unsupported operator {operator.value} for {spec_label(spec_key)}."
    return base


def compute_overall_status(
    requirements: list[StructuredRequirement],
    results: list[RequirementValidationResult],
) -> ValidationStatus:
    for requirement, result in zip(requirements, results, strict=True):
        if not is_must_have(requirement):
            continue
        if result.status == ValidationStatus.FAIL:
            return ValidationStatus.FAIL
    for requirement, result in zip(requirements, results, strict=True):
        if not is_must_have(requirement):
            continue
        if result.status == ValidationStatus.UNKNOWN:
            return ValidationStatus.UNKNOWN
    return ValidationStatus.PASS


def validate_product(
    product: Product,
    requirements: list[StructuredRequirement],
) -> ProductValidationResult:
    lookup = build_spec_lookup(product.specifications)
    results = [
        evaluate_requirement(requirement, lookup.get(requirement.spec_key.value))
        for requirement in requirements
    ]
    return ProductValidationResult(
        product_id=product.id,
        model_number=product.model_number,
        status=compute_overall_status(requirements, results),
        results=results,
    )


def validate_products(
    products: list[Product],
    requirements: list[StructuredRequirement],
) -> list[ProductValidationResult]:
    return [validate_product(product, requirements) for product in products]
