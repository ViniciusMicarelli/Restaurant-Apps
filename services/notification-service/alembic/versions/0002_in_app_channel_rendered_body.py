"""add IN_APP channel + rendered_body column

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
    # `IF NOT EXISTS` (suportado desde PG12) — idempotente em caso de reexecução manual.
    # Não é usado na mesma transação (restrição do Postgres para ALTER TYPE ADD VALUE).
    op.execute("ALTER TYPE notificationchannel ADD VALUE IF NOT EXISTS 'IN_APP'")

    op.add_column(
        "notifications",
        sa.Column("rendered_body", sa.Text(), nullable=False, server_default=""),
    )
    op.alter_column("notifications", "rendered_body", server_default=None)


def downgrade() -> None:
    op.drop_column("notifications", "rendered_body")
    # Postgres não suporta remover um valor de enum — downgrade não reverte o ADD VALUE.
