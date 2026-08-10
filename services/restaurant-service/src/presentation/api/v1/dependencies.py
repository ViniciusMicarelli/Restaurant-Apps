"""Injeção de dependências FastAPI do `restaurant-service`."""

from __future__ import annotations

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
from src.infrastructure.repositories.sqlalchemy_restaurant_repository import (
    SQLAlchemyRestaurantRepository,
)

db_manager = DatabaseManager(settings.db.async_dsn, echo=settings.debug)
redis_client = Redis.from_url(settings.redis.url, decode_responses=True)

get_current_user = build_get_current_user(settings.jwt_secret_key.get_secret_value())


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in db_manager.get_session():
        yield session


def get_rate_limiter() -> RedisRateLimiter:
    return RedisRateLimiter(redis_client, key_prefix="restaurant:rate-limit:")


async def enforce_public_rate_limit(
    request: Request,
    rate_limiter: Annotated[RedisRateLimiter, Depends(get_rate_limiter)],
) -> None:
    """Guard das rotas públicas (bootstrap de tenant, consulta por
    slug/ID — docs/SECURITY.md §2.7, "100 req/min"). Nenhuma delas tem
    `tenant_id` resolvível (a de bootstrap ainda não tem tenant; as
    consultas não exigem `X-Tenant-Id`), então a chave sempre cai pro IP
    do cliente — mesma granularidade que a zona `api_general` do Nginx."""
    key = f"{request.url.path}:{resolve_rate_limit_key(request, trust_proxy_headers=settings.trust_proxy_headers)}"
    allowed = await rate_limiter.hit(
        key,
        max_attempts=settings.public_rate_limit_max_requests,
        window_seconds=settings.public_rate_limit_window_seconds,
    )
    if not allowed:
        raise PublicApiRateLimitExceededError(
            retry_after_seconds=settings.public_rate_limit_window_seconds
        )


def restaurant_repository_for(session: AsyncSession) -> SQLAlchemyRestaurantRepository:
    return SQLAlchemyRestaurantRepository(session)
