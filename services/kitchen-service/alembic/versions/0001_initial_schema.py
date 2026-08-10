"""initial schema: kds_items, kds_logs

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
        "kds_items",
        *_base_columns(),
        sa.Column("order_id", GUID(), nullable=False),
        sa.Column("product_id", GUID(), nullable=False),
        sa.Column("product_name", sa.String(length=150), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column(
            "station",
            sa.Enum("COZINHA_QUENTE", "BAR", "SOBREMESAS", "OUTROS", name="kdsstation"),
            nullable=False,
        ),
        sa.Column("table_number", sa.Integer(), nullable=True),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column(
            "status",
            sa.Enum("PENDING", "PREPARING", "READY", "DELIVERED", name="kdsitemstatus"),
            nullable=False,
        ),
    )
    op.create_index("ix_kds_items_tenant_id", "kds_items", ["tenant_id"])
    op.create_index("ix_kds_items_order_id", "kds_items", ["order_id"])

    op.create_table(
        "kds_logs",
        *_base_columns(),
        sa.Column("kds_item_id", GUID(), nullable=False),
        sa.Column("from_status", sa.Enum(name="kdsitemstatus"), nullable=False),
        sa.Column("to_status", sa.Enum(name="kdsitemstatus"), nullable=False),
    )
    op.create_index("ix_kds_logs_tenant_id", "kds_logs", ["tenant_id"])
    op.create_index("ix_kds_logs_kds_item_id", "kds_logs", ["kds_item_id"])


def downgrade() -> None:
    op.drop_table("kds_logs")
    op.drop_table("kds_items")
    sa.Enum(name="kdsitemstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="kdsstation").drop(op.get_bind(), checkfirst=True)
