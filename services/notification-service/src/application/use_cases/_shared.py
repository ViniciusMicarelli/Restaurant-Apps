"""Helpers compartilhados entre casos de uso do serviço de Notificações."""

from __future__ import annotations

from src.application.dtos.notification_dtos import (
    NotificationResponse,
    NotificationTemplateResponse,
)
from src.domain.entities.notification import Notification
from src.domain.entities.notification_template import NotificationTemplate


def to_template_response(template: NotificationTemplate) -> NotificationTemplateResponse:
    return NotificationTemplateResponse(
        id=template.id,
        tenant_id=template.tenant_id,
        code=template.code,
        channel=template.channel,
        body=template.body,
        subject=template.subject,
    )


def to_notification_response(notification: Notification) -> NotificationResponse:
    return NotificationResponse(
        id=notification.id,
        tenant_id=notification.tenant_id,
        channel=notification.channel,
        recipient=notification.recipient,
        template_code=notification.template_code,
        rendered_body=notification.rendered_body,
        context=notification.context,
        status=notification.status,
        error_message=notification.error_message,
        created_at=notification.created_at,
    )
