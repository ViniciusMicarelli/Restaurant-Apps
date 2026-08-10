"""Caso de uso: cadastro de um template reutilizável de notificação."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from restaurant_core.ids import generate_uuid7
from src.application.dtos.notification_dtos import NotificationTemplateResponse
from src.application.interfaces.repository_interface import (
    NotificationTemplateRepositoryInterface,
)
from src.application.use_cases._shared import to_template_response
from src.domain.entities.notification_template import NotificationChannel, NotificationTemplate
from src.domain.exceptions import DuplicateTemplateCodeException, InvalidTemplateError


@dataclass
class CreateNotificationTemplateUseCase:
    template_repository: NotificationTemplateRepositoryInterface

    async def execute(
        self,
        *,
        tenant_id: uuid.UUID,
        code: str,
        channel: NotificationChannel,
        body: str,
        subject: str | None,
    ) -> NotificationTemplateResponse:
        existing = await self.template_repository.get_by_code(code.strip().upper())
        if existing is not None:
            raise DuplicateTemplateCodeException(code)

        try:
            template = NotificationTemplate(
                id=generate_uuid7(),
                tenant_id=tenant_id,
                code=code,
                channel=channel,
                body=body,
                subject=subject,
            )
        except ValueError as exc:
            raise InvalidTemplateError(str(exc)) from exc

        created = await self.template_repository.add(template)
        return to_template_response(created)
