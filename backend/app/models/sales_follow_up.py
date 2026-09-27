import uuid
from datetime import date
from enum import StrEnum

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class FollowUpPriority(StrEnum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"


class FollowUpStatus(StrEnum):
    OPEN = "OPEN"
    COMPLETED = "COMPLETED"


class SalesFollowUp(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "sales_follow_ups"

    quotation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quotations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_email: Mapped[str] = mapped_column(String(255), nullable=False)
    quotation_number: Mapped[str] = mapped_column(String(32), nullable=False)
    follow_up_date: Mapped[date] = mapped_column(Date, nullable=False)
    priority: Mapped[FollowUpPriority] = mapped_column(String(3), nullable=False)
    status: Mapped[FollowUpStatus] = mapped_column(String(20), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    quotation: Mapped["Quotation"] = relationship("Quotation", back_populates="follow_up")


from app.models.quotation import Quotation  # noqa: E402
