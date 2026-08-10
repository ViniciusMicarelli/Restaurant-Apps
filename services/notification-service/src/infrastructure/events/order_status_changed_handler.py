"""Handler do evento `order.status_changed` — dispara a notificação
"pedido pronto" automaticamente (docs/modules/module_breakdown.md §11).

Antes desta mudança, `notification-service` só existia como API REST — nada
no sistema jamais chamava `POST /api/v1/notifications` automaticamente, então
a fila de notificações nunca era populada de verdade. Agora o serviço também
consome eventos, no mesmo padrão do `kitchen-service` para `order.created`.

Roda fora do escopo de uma requisição HTTP, então abre sua própria sessão de
banco via `DatabaseManager.session()` em vez de depender da injeção do FastAPI.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from restaurant_core.exceptions import ResourceNotFoundException
from restaurant_database import DatabaseManager
from restaurant_events import DomainEvent, EventBus
from src.application.use_cases.queue_notification import QueueNotificationUseCase
from src.domain.entities.notification_template import NotificationChannel
from src.infrastructure.repositories.sqlalchemy_notification_repository import (
    SQLAlchemyNotificationRepository,
)
from src.infrastructure.repositories.sqlalchemy_notification_template_repository import (
    SQLAlchemyNotificationTemplateRepository,
)

logger = logging.getLogger(__name__)

_ORDER_READY_TEMPLATE_CODE = "ORDER_READY"


def build_order_status_changed_handler(
    db_manager: DatabaseManager, event_bus: EventBus
) -> Callable[[DomainEvent], Awaitable[None]]:
    """Fábrica do handler de `order.status_changed`, ligada à infraestrutura do serviço."""

    async def handle_order_status_changed(event: DomainEvent) -> None:
        if event.payload.get("new_status") != "READY":
            return

        table_number = event.payload.get("table_number")
        async with db_manager.session() as session:
            use_case = QueueNotificationUseCase(
                notification_repository=SQLAlchemyNotificationRepository(session, event.tenant_id),
                template_repository=SQLAlchemyNotificationTemplateRepository(
                    session, event.tenant_id
                ),
                event_bus=event_bus,
            )
            try:
                await use_case.execute(
                    tenant_id=event.tenant_id,
                    channel=NotificationChannel.IN_APP,
                    recipient=f"table-{table_number}" if table_number else "salao",
                    template_code=_ORDER_READY_TEMPLATE_CODE,
                    context={"table_number": str(table_number or "-")},
                )
            except ResourceNotFoundException:
                # Tenant ainda não cadastrou o template `ORDER_READY` (ex: novo
                # restaurante sem onboarding completo) — não é um erro fatal do
                # consumidor, só significa "sem notificação configurada ainda".
                logger.info(
                    "Template 'ORDER_READY' ausente para o tenant '%s' — notificação "
                    "de pedido pronto ignorada.",
                    event.tenant_id,
                )
                return
        logger.info(
            "Notificação 'pedido pronto' enfileirada para o pedido '%s'.",
            event.payload.get("order_id"),
        )

    return handle_order_status_changed
