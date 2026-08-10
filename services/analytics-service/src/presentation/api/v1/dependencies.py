"""Injeção de dependências FastAPI do `analytics-service`."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

from restaurant_database import DatabaseManager
from restaurant_events import RabbitMQEventBus
from restaurant_security.rbac import build_get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from src.config import settings
from src.infrastructure.repositories.sqlalchemy_audit_log_repository import (
    SQLAlchemyAuditLogRepository,
)

db_manager = DatabaseManager(settings.db.async_dsn, echo=settings.debug)
event_bus = RabbitMQEventBus(settings.rabbitmq.url)

get_current_user = build_get_current_user(settings.jwt_secret_key.get_secret_value())


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in db_manager.get_session():
        yield session


def audit_log_repository_for(
    session: AsyncSession, tenant_id: uuid.UUID
) -> SQLAlchemyAuditLogRepository:
    return SQLAlchemyAuditLogRepository(session, tenant_id)
