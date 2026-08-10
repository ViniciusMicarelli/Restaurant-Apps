"""make cash_register_id nullable (US-05.4 — customer self-checkout has no register)

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-10
"""

from collections.abc import Sequence

from alembic import op
from restaurant_database.guid import GUID

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column("payments", "cash_register_id", existing_type=GUID(), nullable=True)


def downgrade() -> None:
    op.alter_column("payments", "cash_register_id", existing_type=GUID(), nullable=False)
