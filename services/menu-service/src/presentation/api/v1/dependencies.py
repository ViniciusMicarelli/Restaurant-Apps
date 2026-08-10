"""Injeção de dependências FastAPI do `menu-service`."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Request
from redis.asyncio import Redis
from restaurant_database import DatabaseManager
from restaurant_security.rate_limiter import RedisRateLimiter, resolve_rate_limit_key
from restaurant_security.rbac import build_get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from src.config import settings
from src.domain.exceptions import PublicApiRateLimitExceededError
from src.infrastructure.repositories.sqlalchemy_addon_group_repository import (
    SQLAlchemyAddonGroupRepository,
)
from src.infrastructure.repositories.sqlalchemy_category_repository import (
    SQLAlchemyCategoryRepository,
)
from src.infrastructure.repositories.sqlalchemy_product_repository import (
    SQLAlchemyProductRepository,
)
from src.infrastructure.search.meilisearch_index import MeilisearchProductIndex

db_manager = DatabaseManager(settings.db.async_dsn, echo=settings.debug)
redis_client = Redis.from_url(settings.redis.url, decode_responses=True)
search_index = MeilisearchProductIndex(
    settings.meilisearch_url, settings.meilisearch_master_key.get_secret_value()
)

get_current_user = build_get_current_user(settings.jwt_secret_key.get_secret_value())


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in db_manager.get_session():
        yield session


def get_rate_limiter() -> RedisRateLimiter:
    return RedisRateLimiter(redis_client, key_prefix="menu:rate-limit:")


async def enforce_public_rate_limit(
    request: Request,
    rate_limiter: Annotated[RedisRateLimiter, Depends(get_rate_limiter)],
) -> None:
    """Guard das rotas públicas do cardápio digital (docs/SECURITY.md §2.7 —
    "100 req/min por tenant"). Chave por `tenant_id` (sempre resolvível
    aqui — cardápio digital exige `X-Tenant-Id`) + path."""
    key = f"{request.url.path}:{resolve_rate_limit_key(request)}"
    allowed = await rate_limiter.hit(
        key,
        max_attempts=settings.public_rate_limit_max_requests,
        window_seconds=settings.public_rate_limit_window_seconds,
    )
    if not allowed:
        raise PublicApiRateLimitExceededError(
            retry_after_seconds=settings.public_rate_limit_window_seconds
        )


def category_repository_for(
    session: AsyncSession, tenant_id: uuid.UUID
) -> SQLAlchemyCategoryRepository:
    return SQLAlchemyCategoryRepository(session, tenant_id)


def product_repository_for(
    session: AsyncSession, tenant_id: uuid.UUID
) -> SQLAlchemyProductRepository:
    return SQLAlchemyProductRepository(session, tenant_id)


def addon_group_repository_for(
    session: AsyncSession, tenant_id: uuid.UUID
) -> SQLAlchemyAddonGroupRepository:
    return SQLAlchemyAddonGroupRepository(session, tenant_id)


def get_search_index() -> MeilisearchProductIndex:
    """Dependency FastAPI (permite substituir por um fake nos testes via `dependency_overrides`)."""
    return search_index
