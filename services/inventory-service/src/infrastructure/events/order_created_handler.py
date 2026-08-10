"""Handler do evento `order.created` — baixa automática de insumos (Saga por coreografia).

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
from src.application.use_cases.deduct_stock_for_order import DeductStockForOrderUseCase
from src.infrastructure.repositories.sqlalchemy_inventory_item_repository import (
    SQLAlchemyInventoryItemRepository,
)
from src.infrastructure.repositories.sqlalchemy_recipe_repository import (
    SQLAlchemyRecipeRepository,
)
from src.infrastructure.repositories.sqlalchemy_stock_movement_repository import (
    SQLAlchemyStockMovementRepository,
)

logger = logging.getLogger(__name__)


def build_order_created_handler(
    db_manager: DatabaseManager,
) -> Callable[[DomainEvent], Awaitable[None]]:
    """Fábrica do handler de `order.created`, ligada à infraestrutura do serviço."""

    async def handle_order_created(event: DomainEvent) -> None:
        payload = event.payload
        async with db_manager.session() as session:
            use_case = DeductStockForOrderUseCase(
                inventory_item_repository=SQLAlchemyInventoryItemRepository(
                    session, event.tenant_id
                ),
                recipe_repository=SQLAlchemyRecipeRepository(session, event.tenant_id),
                stock_movement_repository=SQLAlchemyStockMovementRepository(
                    session, event.tenant_id
                ),
            )
            await use_case.execute(
                tenant_id=event.tenant_id,
                order_id=uuid.UUID(str(payload["order_id"])),
                items=list(payload.get("items", [])),
            )
        logger.info("Baixa de estoque processada para o pedido '%s'.", payload.get("order_id"))

    return handle_order_created
