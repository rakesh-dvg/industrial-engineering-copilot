import uuid
from enum import StrEnum

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class DocumentType(StrEnum):
    DATASHEET = "datasheet"
    MANUAL = "manual"
    OTHER = "other"


class IngestStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ProductDocument(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "product_documents"

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType, name="document_type", native_enum=False),
        nullable=False,
        default=DocumentType.DATASHEET,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ingest_status: Mapped[IngestStatus] = mapped_column(
        Enum(IngestStatus, name="ingest_status", native_enum=False),
        nullable=False,
        default=IngestStatus.PENDING,
    )
    ingest_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    product: Mapped["Product"] = relationship("Product", back_populates="documents")
    chunks: Mapped[list["DocumentChunk"]] = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan",
    )


from app.models.document_chunk import DocumentChunk  # noqa: E402
from app.models.product import Product  # noqa: E402
