"""add command_id column to payments (Payment por Comanda)

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from restaurant_database.guid import GUID

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("payments", sa.Column("command_id", GUID(), nullable=True))
    op.create_index("ix_payments_command_id", "payments", ["command_id"])


def downgrade() -> None:
    op.drop_index("ix_payments_command_id", table_name="payments")
    op.drop_column("payments", "command_id")
