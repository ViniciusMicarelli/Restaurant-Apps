"""Injeção de dependências FastAPI do `auth-service`: sessão de banco, Redis,
repositórios tenant-aware/globais e usuário autenticado."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Request
from redis.asyncio import Redis
from restaurant_database import DatabaseManager
from restaurant_security.rate_limiter import RedisRateLimiter
from restaurant_security.rbac import build_get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from src.config import settings
from src.domain.exceptions import RateLimitExceededError
from src.infrastructure.cache.token_blacklist import RedisTokenBlacklist
from src.infrastructure.repositories.sqlalchemy_user_repository import (
    SQLAlchemyUserLookupRepository,
    SQLAlchemyUserRepository,
)

db_manager = DatabaseManager(settings.db.async_dsn, echo=settings.debug)
redis_client = Redis.from_url(settings.redis.url, decode_responses=True)

# Instância única, construída com o segredo JWT do serviço — reaproveitada
# por todas as rotas protegidas (inclusive `require_role(get_current_user, ...)`).
get_current_user = build_get_current_user(settings.jwt_secret_key.get_secret_value())


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in db_manager.get_session():
        yield session


def get_token_blacklist() -> RedisTokenBlacklist:
    return RedisTokenBlacklist(redis_client)


def get_rate_limiter() -> RedisRateLimiter:
    return RedisRateLimiter(redis_client, key_prefix="auth:rate-limit:")


def _extract_client_ip(request: Request) -> str:
    """IP real do cliente pro rate limiter (docs/SECURITY.md §2.7).

    Em produção (`settings.trust_proxy_headers=True`, setado só no
    `docker-compose.prod.yml` — o `auth-service` lá nunca é alcançável a
    não ser via o Nginx do API Gateway), usa o **último** valor de
    `X-Forwarded-For`: o Nginx sempre acrescenta o IP real do cliente como
    o último elo da cadeia (`proxy_set_header X-Forwarded-For
    $proxy_add_x_forwarded_for`) — qualquer valor ANTES desse pode ter sido
    forjado pelo próprio cliente, só o último é confiável.

    Sem isso, `request.client.host` em produção seria sempre o IP interno
    do container Nginx pra todo mundo — a cota "5 tentativas por IP"
    colapsaria pra "5 tentativas pro sistema inteiro" (uma negação de
    serviço trivial e não-intencional contra o próprio login).

    Em dev (sem proxy na frente, `trust_proxy_headers=False` por padrão),
    confiar cegamente no header seria uma forma fácil de burlar o rate
    limiter — qualquer cliente pode setar `X-Forwarded-For` livremente.
    """
    if settings.trust_proxy_headers:
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[-1].strip()
    return request.client.host if request.client else "unknown"


async def enforce_login_rate_limit(
    request: Request,
    rate_limiter: Annotated[RedisRateLimiter, Depends(get_rate_limiter)],
) -> None:
    """Guard de entrada de `/login`/`/login-pin` (docs/SECURITY.md §2.7) —
    cada rota tem seu próprio balde por IP (`request.url.path` faz parte da
    chave), então tentativas numa não consomem a cota da outra."""
    client_ip = _extract_client_ip(request)
    key = f"{request.url.path}:{client_ip}"
    allowed = await rate_limiter.hit(
        key,
        max_attempts=settings.login_rate_limit_max_attempts,
        window_seconds=settings.login_rate_limit_window_seconds,
    )
    if not allowed:
        raise RateLimitExceededError(retry_after_seconds=settings.login_rate_limit_window_seconds)


def get_user_lookup_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> SQLAlchemyUserLookupRepository:
    """Repositório global (sem tenant) — só para login por e-mail e refresh de token."""
    return SQLAlchemyUserLookupRepository(session)


def user_repository_for(session: AsyncSession, tenant_id: uuid.UUID) -> SQLAlchemyUserRepository:
    """Constrói um repositório de usuários escopado a um `tenant_id` específico."""
    return SQLAlchemyUserRepository(session, tenant_id)
