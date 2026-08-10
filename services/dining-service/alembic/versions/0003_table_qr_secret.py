"""add active_qr_secret and qr_secret_expires_at columns to tables

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("tables", sa.Column("active_qr_secret", sa.String(length=64), nullable=True))
    op.add_column(
        "tables", sa.Column("qr_secret_expires_at", sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("tables", "qr_secret_expires_at")
    op.drop_column("tables", "active_qr_secret")
