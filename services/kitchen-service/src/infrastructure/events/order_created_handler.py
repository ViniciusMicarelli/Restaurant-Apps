"""Handler do evento `order.created` — cria os itens do KDS (Saga por coreografia).

Roda fora do escopo de uma requisição HTTP (é chamado pelo `EventBus` a
partir do consumidor RabbitMQ), então abre sua própria sessão de banco via
`DatabaseManager.session()` em vez de depender da injeção do FastAPI.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Awaitable, Callable

from restaurant_database import DatabaseManager
from restaurant_events import DomainEvent
from src.application.interfaces.repository_interface import KDSBroadcasterInterface
from src.application.use_cases.create_kds_items_from_order import (
    CreateKDSItemsFromOrderUseCase,
)
from src.infrastructure.repositories.sqlalchemy_kds_item_repository import (
    SQLAlchemyKDSItemRepository,
)

logger = logging.getLogger(__name__)


def build_order_created_handler(
    db_manager: DatabaseManager, broadcaster: KDSBroadcasterInterface
) -> Callable[[DomainEvent], Awaitable[None]]:
    """Fábrica do handler de `order.created`, ligada à infraestrutura do serviço."""

    async def handle_order_created(event: DomainEvent) -> None:
        payload = event.payload
        async with db_manager.session() as session:
            repository = SQLAlchemyKDSItemRepository(session, event.tenant_id)
            use_case = CreateKDSItemsFromOrderUseCase(
                kds_item_repository=repository, broadcaster=broadcaster
            )
            await use_case.execute(
                tenant_id=event.tenant_id,
                order_id=uuid.UUID(str(payload["order_id"])),
                table_number=payload.get("table_number"),
                items=list(payload.get("items", [])),
            )
        logger.info("Itens do KDS criados a partir do pedido '%s'.", payload.get("order_id"))

    return handle_order_created
