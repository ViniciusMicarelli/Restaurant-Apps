"""add card_last4, card_holder_name, signature_data columns

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
    op.add_column("payments", sa.Column("card_last4", sa.String(length=4), nullable=True))
    op.add_column("payments", sa.Column("card_holder_name", sa.String(length=150), nullable=True))
    op.add_column("payments", sa.Column("signature_data", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("payments", "signature_data")
    op.drop_column("payments", "card_holder_name")
    op.drop_column("payments", "card_last4")
