"""Implementações de `TokenBlacklistInterface` (revogação de JWT via `jti`)."""

from __future__ import annotations

from redis.asyncio import Redis

_BLACKLIST_KEY_PREFIX = "auth:jti:blacklist:"


class RedisTokenBlacklist:
    """Blacklist de `jti` sobre Redis — chave com TTL igual ao tempo restante do token."""

    def __init__(self, redis_client: Redis) -> None:
        self._redis = redis_client

    async def blacklist(self, jti: str, ttl_seconds: int) -> None:
        if ttl_seconds <= 0:
            return
        await self._redis.set(f"{_BLACKLIST_KEY_PREFIX}{jti}", "1", ex=ttl_seconds)

    async def is_blacklisted(self, jti: str) -> bool:
        return await self._redis.exists(f"{_BLACKLIST_KEY_PREFIX}{jti}") > 0


class InMemoryTokenBlacklist:
    """Implementação em memória — usada em testes unitários (sem Redis real)."""

    def __init__(self) -> None:
        self._blacklisted: set[str] = set()

    async def blacklist(self, jti: str, ttl_seconds: int) -> None:
        del ttl_seconds  # TTL não se aplica à implementação em memória (sem expiração)
        self._blacklisted.add(jti)

    async def is_blacklisted(self, jti: str) -> bool:
        return jti in self._blacklisted
