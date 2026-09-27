"""Deterministic commercial calculations for quotations."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

MONEY_QUANT = Decimal("0.01")
MAX_DISCOUNT_PERCENT = Decimal("100")


def money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class LineCalculation:
    line_subtotal: Decimal
    discount_amount: Decimal
    line_total: Decimal


@dataclass(frozen=True)
class QuotationCalculation:
    subtotal: Decimal
    discount_amount: Decimal
    total: Decimal
    lines: tuple[LineCalculation, ...]


def calculate_line(
    quantity: int,
    unit_price: Decimal,
    discount_percent: Decimal,
) -> LineCalculation:
    if quantity <= 0:
        raise ValueError("Quantity must be greater than zero.")
    if unit_price < 0:
        raise ValueError("Unit price cannot be negative.")
    if discount_percent < 0 or discount_percent > MAX_DISCOUNT_PERCENT:
        raise ValueError("Discount percent must be between 0 and 100.")

    gross = money(unit_price * Decimal(quantity))
    discount_amount = money(gross * discount_percent / Decimal("100"))
    line_total = money(gross - discount_amount)
    return LineCalculation(
        line_subtotal=gross,
        discount_amount=discount_amount,
        line_total=line_total,
    )


def calculate_quotation(lines: list[LineCalculation]) -> QuotationCalculation:
    if not lines:
        raise ValueError("At least one line item is required.")

    subtotal = money(sum((line.line_subtotal for line in lines), Decimal("0")))
    discount_amount = money(sum((line.discount_amount for line in lines), Decimal("0")))
    total = money(sum((line.line_total for line in lines), Decimal("0")))
    return QuotationCalculation(
        subtotal=subtotal,
        discount_amount=discount_amount,
        total=total,
        lines=tuple(lines),
    )
