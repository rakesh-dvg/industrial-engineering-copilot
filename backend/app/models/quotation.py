import uuid
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class QuotationStatus(StrEnum):
    DRAFT = "DRAFT"
    REVIEWED = "REVIEWED"
    APPROVED = "APPROVED"
    READY_TO_SEND = "READY_TO_SEND"
    SENT = "SENT"


class Quotation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "quotations"

    quotation_number: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        nullable=False,
        index=True,
    )
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    customer_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[QuotationStatus] = mapped_column(
        String(20),
        nullable=False,
        default=QuotationStatus.DRAFT,
    )
    validity_days: Mapped[int] = mapped_column(Integer, nullable=False)
    lead_time_days: Mapped[int] = mapped_column(Integer, nullable=False)
    technical_status: Mapped[str] = mapped_column(String(20), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    discount_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    validation_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    evidence_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    lines: Mapped[list["QuotationLineItem"]] = relationship(
        "QuotationLineItem",
        back_populates="quotation",
        cascade="all, delete-orphan",
    )
    communication: Mapped["QuotationCommunication | None"] = relationship(
        "QuotationCommunication",
        back_populates="quotation",
        uselist=False,
        cascade="all, delete-orphan",
    )
    follow_up: Mapped["SalesFollowUp | None"] = relationship(
        "SalesFollowUp",
        back_populates="quotation",
        uselist=False,
        cascade="all, delete-orphan",
    )


class QuotationLineItem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "quotation_line_items"

    quotation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quotations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    model_number: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    discount_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    line_subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    quotation: Mapped["Quotation"] = relationship("Quotation", back_populates="lines")


from app.models.quotation_communication import QuotationCommunication  # noqa: E402
from app.models.sales_follow_up import SalesFollowUp  # noqa: E402
