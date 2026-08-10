"""Bridge: consome `notification.requested` (RabbitMQ, Saga por coreografia)
e reenfileira no Dramatiq (Redis) para processamento em segundo plano.

Separa o barramento de eventos de domínio entre serviços (RabbitMQ,
`restaurant_events`) da fila de tarefas em segundo plano de um único
processo de workers (Dramatiq/Redis, ADR-002) — o `notification-service`
publica o evento sem conhecer o Dramatiq; este processo é o único elo entre
os dois mundos, mantendo `services/*` desacoplado da infraestrutura de
`workers/`.

Executado como processo de longa duração: `python -m src.consumers.notification_bridge`.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable

from restaurant_events import DomainEvent, RabbitMQEventBus
from src.async_tasks.notification_actor import send_notification
from src.config import settings

logger = logging.getLogger(__name__)

NOTIFICATION_REQUESTED_ROUTING_KEY = "notification.requested"


def build_notification_requested_handler(
    enqueue: Callable[..., object] = send_notification.send,
) -> Callable[[DomainEvent], Awaitable[None]]:
    """Fábrica do handler — recebe `enqueue` explicitamente para permitir
    testes unitários sem depender de uma conexão Redis real."""

    async def handle_notification_requested(event: DomainEvent) -> None:
        payload = event.payload
        enqueue(
            notification_id=str(payload["notification_id"]),
            channel=str(payload["channel"]),
            recipient=str(payload["recipient"]),
            template_code=str(payload["template_code"]),
            rendered_preview=str(payload["rendered_preview"]),
        )
        logger.info("Notificação '%s' repassada ao Dramatiq.", payload.get("notification_id"))

    return handle_notification_requested


async def run() -> None:  # pragma: no cover - laço de execução real, sem valor de teste unitário
    event_bus = RabbitMQEventBus(settings.rabbitmq.url)
    await event_bus.connect()
    await event_bus.subscribe(
        NOTIFICATION_REQUESTED_ROUTING_KEY,
        build_notification_requested_handler(),
        queue_name="workers.notification.requested",
    )
    logger.info("Bridge de notificações conectada — aguardando eventos.")
    await asyncio.Event().wait()  # mantém o processo vivo consumindo a fila


if __name__ == "__main__":  # pragma: no cover
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run())
