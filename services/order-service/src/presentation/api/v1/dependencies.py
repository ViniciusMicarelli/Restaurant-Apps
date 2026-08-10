"""Injeção de dependências FastAPI do `order-service`."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

from redis.asyncio import Redis
from restaurant_database import DatabaseManager
from restaurant_events import EventBus, RabbitMQEventBus
from restaurant_security.rbac import build_get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from src.config import settings
from src.infrastructure.cache.idempotency_store import RedisIdempotencyStore
from src.infrastructure.repositories.sqlalchemy_order_repository import SQLAlchemyOrderRepository

db_manager = DatabaseManager(settings.db.async_dsn, echo=settings.debug)
redis_client = Redis.from_url(settings.redis.url, decode_responses=True)
event_bus = RabbitMQEventBus(settings.rabbitmq.url)

get_current_user = build_get_current_user(settings.jwt_secret_key.get_secret_value())


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in db_manager.get_session():
        yield session


def order_repository_for(session: AsyncSession, tenant_id: uuid.UUID) -> SQLAlchemyOrderRepository:
    return SQLAlchemyOrderRepository(session, tenant_id)


def get_idempotency_store() -> RedisIdempotencyStore:
    return RedisIdempotencyStore(redis_client)


def get_event_bus() -> EventBus:
    """Dependency FastAPI (permite substituir por `InMemoryEventBus` nos testes)."""
    return event_bus
