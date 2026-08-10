"""Modelo SQLAlchemy 2.0 da tabela `notifications` (`notifications_db`)."""

from __future__ import annotations

from typing import Any

from restaurant_database import TenantAwareModel
from sqlalchemy import JSON, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from src.domain.entities.notification import NotificationStatus
from src.domain.entities.notification_template import NotificationChannel


class NotificationModel(TenantAwareModel):
    __tablename__ = "notifications"

    channel: Mapped[NotificationChannel] = mapped_column(Enum(NotificationChannel), nullable=False)
    recipient: Mapped[str] = mapped_column(String(255), nullable=False)
    template_code: Mapped[str] = mapped_column(String(50), nullable=False)
    rendered_body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    context: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[NotificationStatus] = mapped_column(
        Enum(NotificationStatus), nullable=False, default=NotificationStatus.QUEUED
    )
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
