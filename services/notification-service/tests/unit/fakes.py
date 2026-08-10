"""Fakes em memória dos contratos do `notification-service` — usados pelos testes unitários."""

from __future__ import annotations

import uuid

from src.domain.entities.notification import Notification
from src.domain.entities.notification_template import NotificationTemplate


class FakeTemplateStore:
    def __init__(self, templates: list[NotificationTemplate] | None = None) -> None:
        self._templates: dict[str, NotificationTemplate] = {t.code: t for t in (templates or [])}

    async def get_by_code(self, code: str) -> NotificationTemplate | None:
        return self._templates.get(code.strip().upper())

    async def add(self, template: NotificationTemplate) -> NotificationTemplate:
        self._templates[template.code] = template
        return template


class FakeNotificationStore:
    def __init__(self) -> None:
        self._notifications: dict[uuid.UUID, Notification] = {}

    async def get_by_id(self, notification_id: uuid.UUID) -> Notification | None:
        return self._notifications.get(notification_id)

    async def list_all(self) -> list[Notification]:
        return list(self._notifications.values())

    async def add(self, notification: Notification) -> Notification:
        self._notifications[notification.id] = notification
        return notification
