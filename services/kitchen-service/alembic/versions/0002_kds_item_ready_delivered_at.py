"""add ready_at, delivered_at columns to kds_items

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("kds_items", sa.Column("ready_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("kds_items", sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("kds_items", "delivered_at")
    op.drop_column("kds_items", "ready_at")
