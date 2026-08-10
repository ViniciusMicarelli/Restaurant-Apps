"""initial schema: restaurants

Revision ID: 0001
Revises:
Create Date: 2026-08-04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from restaurant_database.guid import GUID

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "restaurants",
        sa.Column("id", GUID(), primary_key=True, comment="Identificador único universal (UUIDv7)"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("trade_name", sa.String(length=150), nullable=False),
        sa.Column("legal_name", sa.String(length=150), nullable=False),
        sa.Column("cnpj", sa.String(length=18), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("service_fee_percent", sa.Float(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("branding", sa.JSON(), nullable=False),
    )
    op.create_index("ix_restaurants_slug", "restaurants", ["slug"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_restaurants_slug", table_name="restaurants")
    op.drop_table("restaurants")
