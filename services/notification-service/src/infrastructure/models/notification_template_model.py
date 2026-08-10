"""Modelo SQLAlchemy 2.0 da tabela `notification_templates` (`notifications_db`)."""

from __future__ import annotations

from restaurant_database import TenantAwareModel
from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column
from src.domain.entities.notification_template import NotificationChannel


class NotificationTemplateModel(TenantAwareModel):
    __tablename__ = "notification_templates"

    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    channel: Mapped[NotificationChannel] = mapped_column(Enum(NotificationChannel), nullable=False)
    body: Mapped[str] = mapped_column(String(2000), nullable=False)
    subject: Mapped[str | None] = mapped_column(String(200), nullable=True)
