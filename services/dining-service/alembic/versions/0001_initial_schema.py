"""initial schema: tables, commands, queue_entries

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
        "tables",
        *_base_columns(),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("AVAILABLE", "OCCUPIED", "RESERVED", "WAITING_CLEANING", name="tablestatus"),
            nullable=False,
        ),
        sa.Column("qr_code_url", sa.String(length=500), nullable=False),
    )
    op.create_index("ix_tables_tenant_id", "tables", ["tenant_id"])
    op.create_index("ix_tables_number", "tables", ["number"])

    op.create_table(
        "commands",
        *_base_columns(),
        sa.Column("table_id", GUID(), nullable=False),
        sa.Column("waiter_id", GUID(), nullable=False),
        sa.Column("customer_name", sa.String(length=150), nullable=False),
        sa.Column("customer_cpf", sa.String(length=14), nullable=True),
        sa.Column("status", sa.Enum("OPEN", "CLOSED", name="commandstatus"), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_commands_tenant_id", "commands", ["tenant_id"])
    op.create_index("ix_commands_table_id", "commands", ["table_id"])

    op.create_table(
        "queue_entries",
        *_base_columns(),
        sa.Column("customer_name", sa.String(length=150), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=False),
        sa.Column("party_size", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("WAITING", "NOTIFIED", "SEATED", "CANCELLED", name="queuestatus"),
            nullable=False,
        ),
    )
    op.create_index("ix_queue_entries_tenant_id", "queue_entries", ["tenant_id"])


def downgrade() -> None:
    op.drop_table("queue_entries")
    op.drop_table("commands")
    op.drop_table("tables")
    sa.Enum(name="queuestatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="commandstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="tablestatus").drop(op.get_bind(), checkfirst=True)
