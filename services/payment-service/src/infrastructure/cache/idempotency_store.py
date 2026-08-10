"""Implementações de `IdempotencyStoreInterface` (Redis — docs/DATABASE.md)."""

from __future__ import annotations

import uuid

from redis.asyncio import Redis

_KEY_PREFIX = "payments:idempotency:"


class RedisIdempotencyStore:
    def __init__(self, redis_client: Redis) -> None:
        self._redis = redis_client

    async def get_payment_id(self, idempotency_key: str) -> uuid.UUID | None:
        value = await self._redis.get(f"{_KEY_PREFIX}{idempotency_key}")
        return uuid.UUID(str(value)) if value else None

    async def set_payment_id(
        self, idempotency_key: str, payment_id: uuid.UUID, ttl_seconds: int = 86400
    ) -> None:
        await self._redis.set(f"{_KEY_PREFIX}{idempotency_key}", str(payment_id), ex=ttl_seconds)


class InMemoryIdempotencyStore:
    """Implementação em memória — usada em testes (sem Redis real)."""

    def __init__(self) -> None:
        self._store: dict[str, uuid.UUID] = {}

    async def get_payment_id(self, idempotency_key: str) -> uuid.UUID | None:
        return self._store.get(idempotency_key)

    async def set_payment_id(
        self, idempotency_key: str, payment_id: uuid.UUID, ttl_seconds: int = 86400
    ) -> None:
        del ttl_seconds  # TTL não se aplica à implementação em memória
        self._store[idempotency_key] = payment_id
