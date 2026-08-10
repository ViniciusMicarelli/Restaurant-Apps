"""initial schema: cash_registers, cash_movements, payments

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
        "cash_registers",
        *_base_columns(),
        sa.Column("operator_id", GUID(), nullable=False),
        sa.Column("opening_amount", sa.Float(), nullable=False),
        sa.Column("current_balance", sa.Float(), nullable=False),
        sa.Column("status", sa.Enum("OPEN", "CLOSED", name="cashregisterstatus"), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closing_counted_amount", sa.Float(), nullable=True),
        sa.Column("closing_divergence", sa.Float(), nullable=True),
    )
    op.create_index("ix_cash_registers_tenant_id", "cash_registers", ["tenant_id"])
    op.create_index("ix_cash_registers_operator_id", "cash_registers", ["operator_id"])

    op.create_table(
        "cash_movements",
        *_base_columns(),
        sa.Column("cash_register_id", GUID(), nullable=False),
        sa.Column(
            "movement_type",
            sa.Enum("OPENING_FLOAT", "SALE", "SANGRIA", "SUPPLY", name="cashmovementtype"),
            nullable=False,
        ),
        sa.Column("amount_delta", sa.Float(), nullable=False),
        sa.Column("reason", sa.String(length=500), nullable=True),
        sa.Column("payment_id", GUID(), nullable=True),
    )
    op.create_index("ix_cash_movements_tenant_id", "cash_movements", ["tenant_id"])
    op.create_index("ix_cash_movements_cash_register_id", "cash_movements", ["cash_register_id"])

    op.create_table(
        "payments",
        *_base_columns(),
        sa.Column("order_id", GUID(), nullable=False),
        sa.Column("cash_register_id", GUID(), nullable=False),
        sa.Column("splits", sa.JSON(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("PENDING", "APPROVED", "FAILED", "REFUNDED", name="paymentstatus"),
            nullable=False,
        ),
        sa.Column("idempotency_key", sa.String(length=255), nullable=True),
    )
    op.create_index("ix_payments_tenant_id", "payments", ["tenant_id"])
    op.create_index("ix_payments_order_id", "payments", ["order_id"])
    op.create_index("ix_payments_cash_register_id", "payments", ["cash_register_id"])
    op.create_index("ix_payments_idempotency_key", "payments", ["idempotency_key"])


def downgrade() -> None:
    op.drop_table("payments")
    op.drop_table("cash_movements")
    op.drop_table("cash_registers")
    sa.Enum(name="paymentstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="cashmovementtype").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="cashregisterstatus").drop(op.get_bind(), checkfirst=True)
