"""initial schema: notification_templates, notifications

Revision ID: 0001
Revises:
Create Date: 2026-08-05
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
        "notification_templates",
        *_base_columns(),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column(
            "channel",
            sa.Enum("EMAIL", "WHATSAPP", "PUSH", name="notificationchannel"),
            nullable=False,
        ),
        sa.Column("body", sa.String(length=2000), nullable=False),
        sa.Column("subject", sa.String(length=200), nullable=True),
    )
    op.create_index("ix_notification_templates_tenant_id", "notification_templates", ["tenant_id"])
    op.create_index("ix_notification_templates_code", "notification_templates", ["code"])

    op.create_table(
        "notifications",
        *_base_columns(),
        sa.Column(
            "channel",
            sa.Enum("EMAIL", "WHATSAPP", "PUSH", name="notificationchannel"),
            nullable=False,
        ),
        sa.Column("recipient", sa.String(length=255), nullable=False),
        sa.Column("template_code", sa.String(length=50), nullable=False),
        sa.Column("context", sa.JSON(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("QUEUED", "SENT", "FAILED", name="notificationstatus"),
            nullable=False,
        ),
        sa.Column("error_message", sa.String(length=500), nullable=True),
    )
    op.create_index("ix_notifications_tenant_id", "notifications", ["tenant_id"])


def downgrade() -> None:
    op.drop_table("notifications")
    op.drop_table("notification_templates")
    sa.Enum(name="notificationstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="notificationchannel").drop(op.get_bind(), checkfirst=True)
