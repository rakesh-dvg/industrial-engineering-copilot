"""Deterministic unit normalization for engineering validation."""

from __future__ import annotations

import re
from enum import StrEnum


class UnitFamily(StrEnum):
    VOLTAGE = "voltage"
    TEMPERATURE = "temperature"
    CURRENT = "current"
    LENGTH = "length"
    NONE = "none"


def normalize_unit_token(unit: str | None) -> str | None:
    if unit is None:
        return None
    token = unit.strip().lower()
    token = token.replace("°", "")
    token = re.sub(r"\s+", "", token)
    return token or None


def unit_family_for_spec(spec_key: str) -> UnitFamily:
    if spec_key in {"input_voltage", "output_voltage"}:
        return UnitFamily.VOLTAGE
    if spec_key in {"operating_temp_min", "operating_temp_max"}:
        return UnitFamily.TEMPERATURE
    if spec_key == "output_current_max":
        return UnitFamily.CURRENT
    if spec_key == "mounting":
        return UnitFamily.NONE
    return UnitFamily.NONE


def normalize_voltage(value: float, unit: str | None) -> float | None:
    token = normalize_unit_token(unit)
    if token in {None, "v", "volt", "volts"}:
        return value
    if token == "mv":
        return value / 1000.0
    if token == "kv":
        return value * 1000.0
    return None


def normalize_current(value: float, unit: str | None) -> float | None:
    token = normalize_unit_token(unit)
    if token in {None, "a", "amp", "amps"}:
        return value
    if token == "ma":
        return value / 1000.0
    return None


def normalize_temperature(value: float, unit: str | None) -> float | None:
    token = normalize_unit_token(unit)
    if token in {None, "c", "celsius", "degc"}:
        return value
    if token in {"f", "fahrenheit", "degf"}:
        return (value - 32.0) * 5.0 / 9.0
    return None


def normalize_length_mm(value: float, unit: str | None) -> float | None:
    token = normalize_unit_token(unit)
    if token in {None, "mm"}:
        return value
    if token == "cm":
        return value * 10.0
    if token == "m":
        return value * 1000.0
    return None


def normalize_numeric(value: float, unit: str | None, spec_key: str) -> float | None:
    family = unit_family_for_spec(spec_key)
    if family == UnitFamily.VOLTAGE:
        return normalize_voltage(value, unit)
    if family == UnitFamily.TEMPERATURE:
        return normalize_temperature(value, unit)
    if family == UnitFamily.CURRENT:
        return normalize_current(value, unit)
    if family == UnitFamily.LENGTH:
        return normalize_length_mm(value, unit)
    if unit is None or normalize_unit_token(unit) is None:
        return value
    return None
