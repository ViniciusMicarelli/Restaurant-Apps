"""Actor Dramatiq: consome a fila de notificações e "envia" a mensagem.

Escopo Tier B (base sólida, sem integrações externas reais — docs/ai/patterns.md):
um log estruturado substitui a chamada real a um provedor de e-mail/WhatsApp/Push.
Quando uma integração real for adicionada, apenas o corpo desta função muda —
o contrato do actor (assinatura, nome, fila) permanece estável.
"""

from __future__ import annotations

import logging

import dramatiq

logger = logging.getLogger(__name__)


@dramatiq.actor(max_retries=3, queue_name="notifications")
def send_notification(
    notification_id: str,
    channel: str,
    recipient: str,
    template_code: str,
    rendered_preview: str,
) -> None:
    """Processa uma notificação enfileirada (`notification-service` → `.send()`).

    Args:
        notification_id: UUID da `Notification` no `notification-service`.
        channel: Canal de envio (`EMAIL`, `WHATSAPP`, `PUSH`).
        recipient: Destinatário (e-mail, telefone E.164, ou device token).
        template_code: Código do template usado.
        rendered_preview: Corpo já renderizado (placeholders substituídos).
    """
    logger.info(
        "NOTIFICATION_SENT (simulado) notification_id=%s channel=%s recipient=%s "
        "template_code=%s preview=%r",
        notification_id,
        channel,
        recipient,
        template_code,
        rendered_preview,
    )
