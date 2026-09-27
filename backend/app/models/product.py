import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Product(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "products"

    manufacturer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("manufacturers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product_categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    model_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true", nullable=False)

    manufacturer: Mapped["Manufacturer"] = relationship("Manufacturer", back_populates="products")
    category: Mapped["ProductCategory"] = relationship("ProductCategory", back_populates="products")
    specifications: Mapped[list["ProductSpecification"]] = relationship(
        "ProductSpecification",
        back_populates="product",
        cascade="all, delete-orphan",
    )
    pricing: Mapped["ProductPricing | None"] = relationship(
        "ProductPricing",
        back_populates="product",
        cascade="all, delete-orphan",
        uselist=False,
    )
    documents: Mapped[list["ProductDocument"]] = relationship(
        "ProductDocument",
        back_populates="product",
        cascade="all, delete-orphan",
    )
    document_chunks: Mapped[list["DocumentChunk"]] = relationship(
        "DocumentChunk",
        back_populates="product",
        cascade="all, delete-orphan",
    )


from app.models.document_chunk import DocumentChunk  # noqa: E402
from app.models.manufacturer import Manufacturer  # noqa: E402
from app.models.product_category import ProductCategory  # noqa: E402
from app.models.product_document import ProductDocument  # noqa: E402
from app.models.product_pricing import ProductPricing  # noqa: E402
from app.models.product_specification import ProductSpecification  # noqa: E402
