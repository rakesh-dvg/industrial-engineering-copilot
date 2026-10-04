"""Deterministic customer email draft generation for quotations."""

from __future__ import annotations

from decimal import Decimal

from app.models.quotation import Quotation


def _format_money(amount: Decimal, currency: str) -> str:
    return f"{currency} {amount:,.2f}"


def build_email_subject(quotation: Quotation) -> str:
    product_label = quotation.title or "Industrial Products"
    return f"Quotation {quotation.quotation_number} — {product_label}"


def build_email_body(quotation: Quotation) -> str:
    lines = sorted(quotation.lines, key=lambda item: item.created_at)
    primary_line = lines[0] if lines else None
    product_label = primary_line.model_number if primary_line else "See quotation"
    quantity = primary_line.quantity if primary_line else "—"

    body_lines = [
        f"Dear {quotation.customer_name},",
        "",
        "Thank you for your enquiry.",
        "",
        f"Please find our quotation {quotation.quotation_number} for the requested products.",
        "",
        "Quotation details:",
        "",
        f"Product: {product_label}",
        f"Quantity: {quantity}",
        f"Total: {_format_money(quotation.total, quotation.currency)}",
        f"Lead Time: {quotation.lead_time_days} days",
        f"Quotation Validity: {quotation.validity_days} days",
        "",
    ]

    if quotation.technical_status == "PASS":
        body_lines.extend(
            [
                "The proposed product has been technically reviewed against the",
                "requirements provided in your RFQ.",
                "",
            ],
        )

    body_lines.extend(
        [
            "Please let us know if you have any questions or require any",
            "additional information.",
            "",
            "Best regards,",
            "Sales Team",
            "Industrial Engineering Copilot",
        ],
    )
    return "\n".join(body_lines)
