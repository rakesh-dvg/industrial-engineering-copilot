"""Quotation communication and sales follow-up tables for Phase 8.5.

Revision ID: 005_comm_followups
Revises: 004_quotations
Create Date: 2026-09-27
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "005_comm_followups"
down_revision: str | None = "004_quotations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("quotations", sa.Column("customer_email", sa.String(length=255), nullable=True))

    op.create_table(
        "quotation_communications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quotation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("customer_name", sa.String(length=255), nullable=False),
        sa.Column("customer_email", sa.String(length=255), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["quotation_id"], ["quotations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("quotation_id"),
    )
    op.create_index(
        "ix_quotation_communications_quotation_id",
        "quotation_communications",
        ["quotation_id"],
    )

    op.create_table(
        "sales_follow_ups",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quotation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("customer_name", sa.String(length=255), nullable=False),
        sa.Column("customer_email", sa.String(length=255), nullable=False),
        sa.Column("quotation_number", sa.String(length=32), nullable=False),
        sa.Column("follow_up_date", sa.Date(), nullable=False),
        sa.Column("priority", sa.String(length=3), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["quotation_id"], ["quotations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("quotation_id"),
    )
    op.create_index("ix_sales_follow_ups_quotation_id", "sales_follow_ups", ["quotation_id"])


def downgrade() -> None:
    op.drop_table("sales_follow_ups")
    op.drop_table("quotation_communications")
    op.drop_column("quotations", "customer_email")
