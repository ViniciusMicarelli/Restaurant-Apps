"""Implementação concreta de `NotificationTemplateRepositoryInterface` sobre SQLAlchemy 2.0 Async."""

from __future__ import annotations

from restaurant_database import SQLAlchemyRepository
from sqlalchemy import select
from src.domain.entities.notification_template import NotificationTemplate
from src.infrastructure.models.notification_template_model import NotificationTemplateModel


def _to_entity(model: NotificationTemplateModel) -> NotificationTemplate:
    return NotificationTemplate(
        id=model.id,
        tenant_id=model.tenant_id,
        code=model.code,
        channel=model.channel,
        body=model.body,
        subject=model.subject,
    )


class SQLAlchemyNotificationTemplateRepository(SQLAlchemyRepository[NotificationTemplateModel]):
    model = NotificationTemplateModel

    async def get_by_code(self, code: str) -> NotificationTemplate | None:
        stmt = select(self.model).where(
            self.model.code == code.strip().upper(),
            self.model.tenant_id == self._tenant_id,
            self.model.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def add(self, template: NotificationTemplate) -> NotificationTemplate:
        model = NotificationTemplateModel(
            id=template.id,
            tenant_id=template.tenant_id,
            code=template.code,
            channel=template.channel,
            body=template.body,
            subject=template.subject,
        )
        created = await super().add_model(model)
        return _to_entity(created)
