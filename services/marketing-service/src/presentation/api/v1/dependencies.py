"""Injeção de dependências FastAPI do `marketing-service`."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

from restaurant_database import DatabaseManager
from restaurant_security.rbac import build_get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from src.config import settings
from src.infrastructure.repositories.sqlalchemy_coupon_repository import (
    SQLAlchemyCouponRepository,
)

db_manager = DatabaseManager(settings.db.async_dsn, echo=settings.debug)

get_current_user = build_get_current_user(settings.jwt_secret_key.get_secret_value())


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in db_manager.get_session():
        yield session


def coupon_repository_for(
    session: AsyncSession, tenant_id: uuid.UUID
) -> SQLAlchemyCouponRepository:
    return SQLAlchemyCouponRepository(session, tenant_id)
