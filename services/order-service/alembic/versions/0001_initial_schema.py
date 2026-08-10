"""initial schema: orders

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


def _base_columns() -> list[sa.Column]:
    return [
        sa.Column("id", GUID(), primary_key=True, comment="Identificador único universal (UUIDv7)"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", GUID(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "orders",
        *_base_columns(),
        sa.Column(
            "order_type",
            sa.Enum("TABLE", "COUNTER", "QR_CODE", "DELIVERY", name="ordertype"),
            nullable=False,
        ),
        sa.Column("table_number", sa.Integer(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("PENDING", "PREPARING", "READY", "DELIVERED", "CANCELLED", name="orderstatus"),
            nullable=False,
        ),
        sa.Column("items", sa.JSON(), nullable=False),
        sa.Column("cancellation_reason", sa.String(length=500), nullable=True),
    )
    op.create_index("ix_orders_tenant_id", "orders", ["tenant_id"])


def downgrade() -> None:
    op.drop_table("orders")
    sa.Enum(name="orderstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="ordertype").drop(op.get_bind(), checkfirst=True)
