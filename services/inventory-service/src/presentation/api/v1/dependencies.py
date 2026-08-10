"""Injeção de dependências FastAPI do `inventory-service`."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

from restaurant_database import DatabaseManager
from restaurant_events import EventBus, RabbitMQEventBus
from restaurant_security.rbac import build_get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from src.config import settings
from src.infrastructure.repositories.sqlalchemy_inventory_item_repository import (
    SQLAlchemyInventoryItemRepository,
)
from src.infrastructure.repositories.sqlalchemy_recipe_repository import (
    SQLAlchemyRecipeRepository,
)
from src.infrastructure.repositories.sqlalchemy_stock_movement_repository import (
    SQLAlchemyStockMovementRepository,
)
from src.infrastructure.repositories.sqlalchemy_supplier_repository import (
    SQLAlchemySupplierRepository,
)

db_manager = DatabaseManager(settings.db.async_dsn, echo=settings.debug)
event_bus = RabbitMQEventBus(settings.rabbitmq.url)

get_current_user = build_get_current_user(settings.jwt_secret_key.get_secret_value())


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in db_manager.get_session():
        yield session


def inventory_item_repository_for(
    session: AsyncSession, tenant_id: uuid.UUID
) -> SQLAlchemyInventoryItemRepository:
    return SQLAlchemyInventoryItemRepository(session, tenant_id)


def supplier_repository_for(
    session: AsyncSession, tenant_id: uuid.UUID
) -> SQLAlchemySupplierRepository:
    return SQLAlchemySupplierRepository(session, tenant_id)


def recipe_repository_for(
    session: AsyncSession, tenant_id: uuid.UUID
) -> SQLAlchemyRecipeRepository:
    return SQLAlchemyRecipeRepository(session, tenant_id)


def stock_movement_repository_for(
    session: AsyncSession, tenant_id: uuid.UUID
) -> SQLAlchemyStockMovementRepository:
    return SQLAlchemyStockMovementRepository(session, tenant_id)


def get_event_bus() -> EventBus:
    """Dependency FastAPI (permite substituir por `InMemoryEventBus` nos testes)."""
    return event_bus
