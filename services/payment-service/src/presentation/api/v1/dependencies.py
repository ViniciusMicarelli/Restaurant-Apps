"""Injeção de dependências FastAPI do `payment-service`."""

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
from src.infrastructure.cache.idempotency_store import RedisIdempotencyStore
from src.infrastructure.clients.dining_service_client import HttpxDiningServiceClient
from src.infrastructure.clients.order_service_client import HttpxOrderServiceClient
from src.infrastructure.clients.restaurant_service_client import HttpxRestaurantServiceClient
from src.infrastructure.repositories.sqlalchemy_cash_movement_repository import (
    SQLAlchemyCashMovementRepository,
)
from src.infrastructure.repositories.sqlalchemy_cash_register_repository import (
    SQLAlchemyCashRegisterRepository,
)
from src.infrastructure.repositories.sqlalchemy_payment_repository import (
    SQLAlchemyPaymentRepository,
)

db_manager = DatabaseManager(settings.db.async_dsn, echo=settings.debug)
redis_client = Redis.from_url(settings.redis.url, decode_responses=True)

get_current_user = build_get_current_user(settings.jwt_secret_key.get_secret_value())


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in db_manager.get_session():
        yield session


def cash_register_repository_for(
    session: AsyncSession, tenant_id: uuid.UUID
) -> SQLAlchemyCashRegisterRepository:
    return SQLAlchemyCashRegisterRepository(session, tenant_id)


def cash_movement_repository_for(
    session: AsyncSession, tenant_id: uuid.UUID
) -> SQLAlchemyCashMovementRepository:
    return SQLAlchemyCashMovementRepository(session, tenant_id)


def payment_repository_for(
    session: AsyncSession, tenant_id: uuid.UUID
) -> SQLAlchemyPaymentRepository:
    return SQLAlchemyPaymentRepository(session, tenant_id)


def get_idempotency_store() -> RedisIdempotencyStore:
    return RedisIdempotencyStore(redis_client)


def get_rate_limiter() -> RedisRateLimiter:
    return RedisRateLimiter(redis_client, key_prefix="payment:rate-limit:")


async def enforce_public_rate_limit(
    request: Request,
    rate_limiter: Annotated[RedisRateLimiter, Depends(get_rate_limiter)],
) -> None:
    """Guard da rota pública do autoatendimento (docs/SECURITY.md §2.7 —
    "100 req/min por tenant"). Chave por `tenant_id` (sempre resolvível
    aqui — `customer-checkout` exige `X-Tenant-Id`) + path."""
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


dining_service_client = HttpxDiningServiceClient(settings.dining_service_url)
order_service_client = HttpxOrderServiceClient(settings.order_service_url)
restaurant_service_client = HttpxRestaurantServiceClient(settings.restaurant_service_url)


def get_dining_service_client() -> HttpxDiningServiceClient:
    return dining_service_client


def get_order_service_client() -> HttpxOrderServiceClient:
    return order_service_client


def get_restaurant_service_client() -> HttpxRestaurantServiceClient:
    return restaurant_service_client
