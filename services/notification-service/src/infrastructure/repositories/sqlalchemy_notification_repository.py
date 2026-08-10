"""Implementação concreta de `NotificationRepositoryInterface` sobre SQLAlchemy 2.0 Async."""

from __future__ import annotations

import uuid

from restaurant_database import SQLAlchemyRepository
from src.domain.entities.notification import Notification
from src.infrastructure.models.notification_model import NotificationModel


def _to_entity(model: NotificationModel) -> Notification:
    return Notification(
        id=model.id,
        tenant_id=model.tenant_id,
        channel=model.channel,
        recipient=model.recipient,
        template_code=model.template_code,
        rendered_body=model.rendered_body,
        context=dict(model.context),
        status=model.status,
        error_message=model.error_message,
        created_at=model.created_at,
    )


class SQLAlchemyNotificationRepository(SQLAlchemyRepository[NotificationModel]):
    model = NotificationModel

    async def get_by_id(self, notification_id: uuid.UUID) -> Notification | None:
        model = await super().get_model_by_id(notification_id)
        return _to_entity(model) if model is not None else None

    async def list_all(self) -> list[Notification]:
        models = await super().list_models(limit=1000)
        return [_to_entity(m) for m in models]

    async def add(self, notification: Notification) -> Notification:
        model = NotificationModel(
            id=notification.id,
            tenant_id=notification.tenant_id,
            channel=notification.channel,
            recipient=notification.recipient,
            template_code=notification.template_code,
            rendered_body=notification.rendered_body,
            context=notification.context,
            status=notification.status,
            error_message=notification.error_message,
        )
        created = await super().add_model(model)
        return _to_entity(created)
