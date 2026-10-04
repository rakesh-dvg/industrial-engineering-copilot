import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class CommunicationStatus(StrEnum):
    DRAFT = "DRAFT"
    READY_TO_SEND = "READY_TO_SEND"
    SENT = "SENT"


class QuotationCommunication(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "quotation_communications"

    quotation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quotations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_email: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[CommunicationStatus] = mapped_column(
        String(20),
        nullable=False,
        default=CommunicationStatus.DRAFT,
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    quotation: Mapped["Quotation"] = relationship("Quotation", back_populates="communication")


from app.models.quotation import Quotation  # noqa: E402
