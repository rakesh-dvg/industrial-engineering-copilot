"""Product catalog: manufacturers, categories, products, specs, pricing.

Revision ID: 002_product_catalog
Revises: 001_initial_foundation
Create Date: 2026-09-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "002_product_catalog"
down_revision: str | None = "001_initial_foundation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "manufacturers",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("website", sa.String(length=500), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_manufacturers_name", "manufacturers", ["name"], unique=True)

    op.create_table(
        "product_categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_product_categories_slug", "product_categories", ["slug"], unique=True)

    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("manufacturer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("model_number", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["product_categories.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["manufacturer_id"], ["manufacturers.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("model_number"),
    )
    op.create_index("ix_products_category_id", "products", ["category_id"], unique=False)
    op.create_index("ix_products_manufacturer_id", "products", ["manufacturer_id"], unique=False)
    op.create_index("ix_products_model_number", "products", ["model_number"], unique=True)

    op.create_table(
        "product_specifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("spec_key", sa.String(length=100), nullable=False),
        sa.Column("numeric_value", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("text_value", sa.String(length=500), nullable=True),
        sa.Column("boolean_value", sa.Boolean(), nullable=True),
        sa.Column("unit", sa.String(length=50), nullable=True),
        sa.Column("source", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_id", "spec_key", name="uq_product_spec_key"),
    )
    op.create_index("ix_product_specifications_product_id", "product_specifications", ["product_id"], unique=False)
    op.create_index("ix_product_specifications_spec_key", "product_specifications", ["spec_key"], unique=False)

    op.create_table(
        "product_pricing",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("unit_price", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="USD", nullable=False),
        sa.Column("discount_percent", sa.Numeric(precision=5, scale=2), server_default="0", nullable=False),
        sa.Column("lead_time_days", sa.Integer(), nullable=False),
        sa.Column("price_valid_until", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_id"),
    )
    op.create_index("ix_product_pricing_product_id", "product_pricing", ["product_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_product_pricing_product_id", table_name="product_pricing")
    op.drop_table("product_pricing")
    op.drop_index("ix_product_specifications_spec_key", table_name="product_specifications")
    op.drop_index("ix_product_specifications_product_id", table_name="product_specifications")
    op.drop_table("product_specifications")
    op.drop_index("ix_products_model_number", table_name="products")
    op.drop_index("ix_products_manufacturer_id", table_name="products")
    op.drop_index("ix_products_category_id", table_name="products")
    op.drop_table("products")
    op.drop_index("ix_product_categories_slug", table_name="product_categories")
    op.drop_table("product_categories")
    op.drop_index("ix_manufacturers_name", table_name="manufacturers")
    op.drop_table("manufacturers")
