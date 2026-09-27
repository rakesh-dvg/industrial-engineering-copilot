from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Manufacturer(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "manufacturers"

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true", nullable=False)

    products: Mapped[list["Product"]] = relationship("Product", back_populates="manufacturer")


from app.models.product import Product  # noqa: E402
