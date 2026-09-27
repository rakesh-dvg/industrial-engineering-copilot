import uuid
from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class ProductSpecification(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "product_specifications"
    __table_args__ = (UniqueConstraint("product_id", "spec_key", name="uq_product_spec_key"),)

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    spec_key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    numeric_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    text_value: Mapped[str | None] = mapped_column(String(500), nullable=True)
    boolean_value: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)

    product: Mapped["Product"] = relationship("Product", back_populates="specifications")


from app.models.product import Product  # noqa: E402
