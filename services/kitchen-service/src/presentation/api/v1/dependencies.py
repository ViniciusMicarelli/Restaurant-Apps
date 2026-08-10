"""Injeção de dependências FastAPI do `kitchen-service`."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

from restaurant_database import DatabaseManager
from restaurant_events import EventBus, RabbitMQEventBus
from restaurant_security.rbac import build_get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from src.config import settings
from src.infrastructure.repositories.sqlalchemy_kds_item_repository import (
    SQLAlchemyKDSItemRepository,
)
from src.infrastructure.repositories.sqlalchemy_kds_log_repository import (
    SQLAlchemyKDSLogRepository,
)
from src.infrastructure.websocket.connection_manager import KDSConnectionManager

db_manager = DatabaseManager(settings.db.async_dsn, echo=settings.debug)
event_bus = RabbitMQEventBus(settings.rabbitmq.url)
connection_manager = KDSConnectionManager()

get_current_user = build_get_current_user(settings.jwt_secret_key.get_secret_value())


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in db_manager.get_session():
        yield session


def kds_item_repository_for(
    session: AsyncSession, tenant_id: uuid.UUID
) -> SQLAlchemyKDSItemRepository:
    return SQLAlchemyKDSItemRepository(session, tenant_id)


def kds_log_repository_for(
    session: AsyncSession, tenant_id: uuid.UUID
) -> SQLAlchemyKDSLogRepository:
    return SQLAlchemyKDSLogRepository(session, tenant_id)


def get_broadcaster() -> KDSConnectionManager:
    """Dependency FastAPI (permite substituir por um fake nos testes)."""
    return connection_manager


def get_event_bus() -> EventBus:
    """Dependency FastAPI (permite substituir por `InMemoryEventBus` nos testes)."""
    return event_bus
