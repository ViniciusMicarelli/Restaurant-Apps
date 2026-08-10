"""Entidade `NotificationTemplate` — modelo reutilizável de mensagem (docs/modules/module_breakdown.md §11)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from enum import StrEnum


class NotificationChannel(StrEnum):
    EMAIL = "EMAIL"
    WHATSAPP = "WHATSAPP"
    PUSH = "PUSH"
    IN_APP = "IN_APP"  # sino de notificações dentro do admin-web (sem provedor externo)


@dataclass
class NotificationTemplate:
    """Modelo de mensagem reutilizável, associado a um canal de envio.

    O corpo (`body`) usa placeholders `{chave}` substituídos pelo `context`
    fornecido em cada `Notification` enfileirada (ex: `"Olá {nome_cliente}..."`).
    """

    id: uuid.UUID
    tenant_id: uuid.UUID
    code: str
    channel: NotificationChannel
    body: str
    subject: str | None = None

    def __post_init__(self) -> None:
        self.code = self.code.strip().upper()
        if not self.code:
            raise ValueError("O código do template não pode ser vazio.")
        if not self.body.strip():
            raise ValueError("O corpo do template não pode ser vazio.")
        if self.channel == NotificationChannel.EMAIL and not (
            self.subject and self.subject.strip()
        ):
            raise ValueError("Templates de e-mail exigem um assunto (`subject`).")

    def render(self, context: dict[str, str]) -> str:
        """Substitui os placeholders `{chave}` do corpo pelos valores do contexto."""
        try:
            return self.body.format(**context)
        except KeyError as exc:
            msg = f"Contexto incompleto para o template '{self.code}': chave ausente {exc}."
            raise ValueError(msg) from exc
