"""initial schema: deliveries

Revision ID: 0001
Revises:
Create Date: 2026-08-05
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
        "deliveries",
        *_base_columns(),
        sa.Column("order_id", GUID(), nullable=False),
        sa.Column("delivery_address", sa.String(length=500), nullable=False),
        sa.Column("courier_name", sa.String(length=150), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "PENDING", "ASSIGNED", "IN_TRANSIT", "DELIVERED", "CANCELLED", name="deliverystatus"
            ),
            nullable=False,
        ),
    )
    op.create_index("ix_deliveries_tenant_id", "deliveries", ["tenant_id"])
    op.create_index("ix_deliveries_order_id", "deliveries", ["order_id"])


def downgrade() -> None:
    op.drop_table("deliveries")
    sa.Enum(name="deliverystatus").drop(op.get_bind(), checkfirst=True)
