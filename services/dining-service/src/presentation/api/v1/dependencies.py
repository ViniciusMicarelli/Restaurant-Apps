"""Injeção de dependências FastAPI do `dining-service`."""

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
from src.infrastructure.repositories.sqlalchemy_command_repository import (
    SQLAlchemyCommandRepository,
)
from src.infrastructure.repositories.sqlalchemy_queue_repository import SQLAlchemyQueueRepository
from src.infrastructure.repositories.sqlalchemy_table_repository import SQLAlchemyTableRepository

db_manager = DatabaseManager(settings.db.async_dsn, echo=settings.debug)
redis_client = Redis.from_url(settings.redis.url, decode_responses=True)

get_current_user = build_get_current_user(settings.jwt_secret_key.get_secret_value())


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in db_manager.get_session():
        yield session


def get_rate_limiter() -> RedisRateLimiter:
    return RedisRateLimiter(redis_client, key_prefix="dining:rate-limit:")


async def enforce_public_rate_limit(
    request: Request,
    rate_limiter: Annotated[RedisRateLimiter, Depends(get_rate_limiter)],
) -> None:
    """Guard das rotas públicas do autoatendimento do cliente
    (docs/SECURITY.md §2.7 — "100 req/min por tenant"). Chave por
    `tenant_id` (sempre resolvível aqui via `X-Tenant-Id`, exigido por
    `require_tenant_id` nas próprias rotas) + path, mesmo padrão de balde
    independente por rota já usado no rate limit de login do `auth-service`.
    """
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


def table_repository_for(session: AsyncSession, tenant_id: uuid.UUID) -> SQLAlchemyTableRepository:
    return SQLAlchemyTableRepository(session, tenant_id)


def command_repository_for(
    session: AsyncSession, tenant_id: uuid.UUID
) -> SQLAlchemyCommandRepository:
    return SQLAlchemyCommandRepository(session, tenant_id)


def queue_repository_for(session: AsyncSession, tenant_id: uuid.UUID) -> SQLAlchemyQueueRepository:
    return SQLAlchemyQueueRepository(session, tenant_id)
