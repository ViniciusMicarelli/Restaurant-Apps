"""Teste de integração do handler do evento `order.created` (Saga por coreografia).

Usa um `DatabaseManager` próprio (SQLite em memória) — não depende do FastAPI
nem do RabbitMQ real, apenas do contrato `EventBus`/`DomainEvent`.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from restaurant_core.ids import generate_uuid7
from restaurant_database import DatabaseManager
from restaurant_database.base import BaseDBModel
from restaurant_events import DomainEvent
from src.domain.entities.inventory_item import InventoryItem, InventoryUnit
from src.domain.entities.recipe import Recipe, RecipeItem
from src.infrastructure.events.order_created_handler import build_order_created_handler
from src.infrastructure.repositories.sqlalchemy_inventory_item_repository import (
    SQLAlchemyInventoryItemRepository,
)
from src.infrastructure.repositories.sqlalchemy_recipe_repository import (
    SQLAlchemyRecipeRepository,
)
from src.infrastructure.repositories.sqlalchemy_stock_movement_repository import (
    SQLAlchemyStockMovementRepository,
)


@pytest_asyncio.fixture
async def db_manager() -> AsyncGenerator[DatabaseManager, None]:
    manager = DatabaseManager("sqlite+aiosqlite:///:memory:")
    async with manager.engine.begin() as conn:
        await conn.run_sync(BaseDBModel.metadata.create_all)
    yield manager
    await manager.close()


@pytest.mark.asyncio
async def test_order_created_event_deducts_stock_per_recipe(db_manager: DatabaseManager) -> None:
    tenant_id, order_id, product_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()

    # Arrange: cadastra o insumo e a ficha técnica do produto vendido.
    async with db_manager.session() as session:
        item_repository = SQLAlchemyInventoryItemRepository(session, tenant_id)
        inventory_item = await item_repository.add(
            InventoryItem(
                id=generate_uuid7(),
                tenant_id=tenant_id,
                name="Pão",
                unit=InventoryUnit.UN,
                current_quantity=100.0,
            )
        )
        await SQLAlchemyRecipeRepository(session, tenant_id).add(
            Recipe(
                id=generate_uuid7(),
                tenant_id=tenant_id,
                product_id=product_id,
                items=[RecipeItem(inventory_item_id=inventory_item.id, quantity_required=2.0)],
            )
        )

    handler = build_order_created_handler(db_manager)
    event = DomainEvent(
        event_type="order.created",
        tenant_id=tenant_id,
        payload={
            "order_id": str(order_id),
            "items": [{"product_id": str(product_id), "product_name": "X-Burger", "quantity": 3}],
        },
    )

    # Act
    await handler(event)

    # Assert
    async with db_manager.session() as session:
        updated_item = await SQLAlchemyInventoryItemRepository(session, tenant_id).get_by_id(
            inventory_item.id
        )
        movements = await SQLAlchemyStockMovementRepository(session, tenant_id).list_by_item(
            inventory_item.id
        )

    assert updated_item is not None
    assert updated_item.current_quantity == 94.0  # 100 - (2 * 3)
    assert len(movements) == 1
    assert movements[0].order_id == order_id
