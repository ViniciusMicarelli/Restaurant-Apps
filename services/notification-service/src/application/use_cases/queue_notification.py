"""Caso de uso: enfileiramento de uma notificação para envio assíncrono.

Publica o evento `notification.requested` (`restaurant_events`), consumido
pelo worker `notification_actor` (Dramatiq) que "envia" a mensagem — nesta
fase, um log estruturado substitui a integração real de e-mail/WhatsApp
(docs/ai/patterns.md — Tier B: base sólida, sem integrações externas).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from restaurant_core.exceptions import ResourceNotFoundException
from restaurant_core.ids import generate_uuid7
from restaurant_events import DomainEvent, EventBus
from src.application.dtos.notification_dtos import NotificationResponse
from src.application.interfaces.repository_interface import (
    NotificationRepositoryInterface,
    NotificationTemplateRepositoryInterface,
)
from src.application.use_cases._shared import to_notification_response
from src.domain.entities.notification import Notification
from src.domain.entities.notification_template import NotificationChannel
from src.domain.exceptions import ChannelMismatchException, TemplateContextError

NOTIFICATION_REQUESTED_ROUTING_KEY = "notification.requested"


@dataclass
class QueueNotificationUseCase:
    notification_repository: NotificationRepositoryInterface
    template_repository: NotificationTemplateRepositoryInterface
    event_bus: EventBus

    async def execute(
        self,
        *,
        tenant_id: uuid.UUID,
        channel: NotificationChannel,
        recipient: str,
        template_code: str,
        context: dict[str, str],
    ) -> NotificationResponse:
        template = await self.template_repository.get_by_code(template_code.strip().upper())
        if template is None:
            raise ResourceNotFoundException("NotificationTemplate", template_code)
        if template.channel != channel:
            raise ChannelMismatchException(template.code)

        try:
            rendered_preview = template.render(context)
        except ValueError as exc:
            raise TemplateContextError(str(exc)) from exc

        notification = Notification(
            id=generate_uuid7(),
            tenant_id=tenant_id,
            channel=channel,
            recipient=recipient,
            template_code=template.code,
            rendered_body=rendered_preview,
            context=context,
        )
        created = await self.notification_repository.add(notification)

        await self.event_bus.publish(
            DomainEvent(
                event_type=NOTIFICATION_REQUESTED_ROUTING_KEY,
                tenant_id=tenant_id,
                payload={
                    "notification_id": str(created.id),
                    "channel": channel.value,
                    "recipient": recipient,
                    "template_code": template.code,
                    "rendered_preview": rendered_preview,
                },
            ),
            routing_key=NOTIFICATION_REQUESTED_ROUTING_KEY,
        )

        return to_notification_response(created)


@dataclass
class ListNotificationsUseCase:
    notification_repository: NotificationRepositoryInterface

    async def execute(self) -> list[NotificationResponse]:
        notifications = await self.notification_repository.list_all()
        return [to_notification_response(n) for n in notifications]
