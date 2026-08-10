"""add command_id column

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from restaurant_database.guid import GUID

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("command_id", GUID(), nullable=True))
    op.create_index("ix_orders_command_id", "orders", ["command_id"])


def downgrade() -> None:
    op.drop_index("ix_orders_command_id", table_name="orders")
    op.drop_column("orders", "command_id")
