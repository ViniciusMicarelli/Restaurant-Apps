"""Injeção de dependências FastAPI do `delivery-service`."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

from restaurant_database import DatabaseManager
from restaurant_security.rbac import build_get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from src.application.interfaces.repository_interface import ExternalDeliveryProviderInterface
from src.config import settings
from src.infrastructure.providers.not_implemented_provider import (
    NotImplementedExternalDeliveryProvider,
)
from src.infrastructure.repositories.sqlalchemy_delivery_repository import (
    SQLAlchemyDeliveryRepository,
)

db_manager = DatabaseManager(settings.db.async_dsn, echo=settings.debug)
external_delivery_provider = NotImplementedExternalDeliveryProvider()

get_current_user = build_get_current_user(settings.jwt_secret_key.get_secret_value())


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in db_manager.get_session():
        yield session


def delivery_repository_for(
    session: AsyncSession, tenant_id: uuid.UUID
) -> SQLAlchemyDeliveryRepository:
    return SQLAlchemyDeliveryRepository(session, tenant_id)


def get_external_delivery_provider() -> ExternalDeliveryProviderInterface:
    """Dependency FastAPI (permite substituir por um fake real nos testes/futuro)."""
    return external_delivery_provider
