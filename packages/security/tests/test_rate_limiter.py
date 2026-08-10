"""Testes do rate limiter compartilhado (docs/SECURITY.md §2.7) — contrato
exercitado via `InMemoryRateLimiter` (mesma interface de `RedisRateLimiter`,
sem depender de Redis real), mais a resolução de chave `resolve_rate_limit_key`
usada pelas rotas públicas de `dining`/`menu`/`payment`/`restaurant-service`.

Movido de `auth-service` (onde nasceu, protegendo só `/login`) quando o
mesmo padrão passou a ser reaproveitado por mais serviços — 2026-08-10.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from restaurant_security.rate_limiter import InMemoryRateLimiter, resolve_rate_limit_key
from restaurant_security.tenant_context import TenantContextMiddleware

SECRET = "test-secret-key-32-chars-long-security"


@pytest.mark.asyncio
async def test_allows_up_to_max_attempts() -> None:
    limiter = InMemoryRateLimiter()

    results = [await limiter.hit("ip-1", max_attempts=5, window_seconds=60) for _ in range(5)]

    assert all(results)


@pytest.mark.asyncio
async def test_blocks_the_attempt_after_max_attempts() -> None:
    limiter = InMemoryRateLimiter()
    for _ in range(5):
        await limiter.hit("ip-1", max_attempts=5, window_seconds=60)

    sixth = await limiter.hit("ip-1", max_attempts=5, window_seconds=60)

    assert sixth is False


@pytest.mark.asyncio
async def test_different_keys_have_independent_buckets() -> None:
    limiter = InMemoryRateLimiter()
    for _ in range(5):
        await limiter.hit("ip-1", max_attempts=5, window_seconds=60)

    still_allowed = await limiter.hit("ip-2", max_attempts=5, window_seconds=60)

    assert still_allowed is True


@pytest.mark.asyncio
async def test_reset_clears_all_buckets() -> None:
    limiter = InMemoryRateLimiter()
    for _ in range(5):
        await limiter.hit("ip-1", max_attempts=5, window_seconds=60)

    limiter.reset()

    assert await limiter.hit("ip-1", max_attempts=5, window_seconds=60) is True


def _build_test_app(*, trust_proxy_headers: bool = False) -> FastAPI:
    app = FastAPI()
    app.add_middleware(TenantContextMiddleware, jwt_secret_key=SECRET)

    @app.get("/key")
    async def _key(request: Request) -> dict[str, str]:
        return {"key": resolve_rate_limit_key(request, trust_proxy_headers=trust_proxy_headers)}

    return app


def test_resolve_rate_limit_key_uses_tenant_id_when_resolved() -> None:
    client = TestClient(_build_test_app())
    tenant_id = str(uuid.uuid4())

    response = client.get("/key", headers={"X-Tenant-Id": tenant_id})

    assert response.json() == {"key": f"tenant:{tenant_id}"}


def test_resolve_rate_limit_key_falls_back_to_client_ip_without_tenant() -> None:
    client = TestClient(_build_test_app())

    response = client.get("/key")

    assert response.json()["key"].startswith("ip:")


def test_resolve_rate_limit_key_ignores_forwarded_for_when_proxy_not_trusted() -> None:
    client = TestClient(_build_test_app(trust_proxy_headers=False))

    response = client.get("/key", headers={"X-Forwarded-For": "203.0.113.9"})

    # Sem confiar no proxy, a chave usa o IP de conexão real do TestClient,
    # nunca o header forjável.
    assert response.json()["key"] != "ip:203.0.113.9"


def test_resolve_rate_limit_key_uses_last_forwarded_for_when_proxy_trusted() -> None:
    client = TestClient(_build_test_app(trust_proxy_headers=True))

    response = client.get("/key", headers={"X-Forwarded-For": "203.0.113.9, 10.0.0.5"})

    # Só o último elo da cadeia é confiável (o que o Nginx do Gateway
    # garante ter sido acrescentado por ele mesmo, não forjável pelo cliente).
    assert response.json() == {"key": "ip:10.0.0.5"}
