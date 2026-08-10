"""Contratos de repositório do serviço de Notificações."""

from __future__ import annotations

import uuid
from typing import Protocol

from src.domain.entities.notification import Notification
from src.domain.entities.notification_template import NotificationTemplate


class NotificationTemplateRepositoryInterface(Protocol):
    async def get_by_code(self, code: str) -> NotificationTemplate | None: ...

    async def add(self, template: NotificationTemplate) -> NotificationTemplate: ...


class NotificationRepositoryInterface(Protocol):
    async def get_by_id(self, notification_id: uuid.UUID) -> Notification | None: ...

    async def list_all(self) -> list[Notification]: ...

    async def add(self, notification: Notification) -> Notification: ...
