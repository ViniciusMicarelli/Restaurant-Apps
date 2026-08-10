"""Entidade `Notification` — mensagem enfileirada para envio assíncrono (docs/modules/module_breakdown.md §11)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from src.domain.entities.notification_template import NotificationChannel


class NotificationStatus(StrEnum):
    QUEUED = "QUEUED"  # Persistida e publicada para a fila (Dramatiq/RabbitMQ)
    SENT = "SENT"  # Processada pelo worker (docs/ai/patterns.md — log estruturado)
    FAILED = "FAILED"  # Falha reportada pelo worker


@dataclass
class Notification:
    """Uma notificação enfileirada para disparo assíncrono por um worker.

    Attributes:
        id: UUIDv7 da notificação.
        tenant_id: ID do restaurante proprietário.
        channel: Canal de envio (deve corresponder ao canal do template).
        recipient: Destinatário (e-mail, telefone E.164, ou device token).
        template_code: Código do `NotificationTemplate` usado.
        context: Valores para substituição dos placeholders do template.
        rendered_body: Texto já renderizado (template + context) no momento do
            enfileiramento — persistido para exibição direta (ex: sino do
            admin-web) sem precisar buscar o template de novo.
        status: Estado atual do envio.
        error_message: Motivo da falha, se `status == FAILED`.
    """

    id: uuid.UUID
    tenant_id: uuid.UUID
    channel: NotificationChannel
    recipient: str
    template_code: str
    rendered_body: str
    context: dict[str, str] = field(default_factory=dict)
    status: NotificationStatus = NotificationStatus.QUEUED
    error_message: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if not self.recipient.strip():
            raise ValueError("O destinatário da notificação não pode ser vazio.")
        self.template_code = self.template_code.strip().upper()
        if not self.template_code:
            raise ValueError("O código do template não pode ser vazio.")
