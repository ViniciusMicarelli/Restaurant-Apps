"""Rate limiting das rotas públicas (docs/SECURITY.md §2.7 — "100 req/min").
Nenhuma delas tem tenant resolvível (bootstrap de tenant + consultas por
slug/ID, sem `X-Tenant-Id`) — a chave cai sempre pro IP do cliente, então
(ao contrário de `dining`/`menu`/`payment`) o balde aqui é compartilhado
por qualquer requisição vinda do mesmo `TestClient` nesse path, não por
tenant. Monkeypatcha o teto pra um número pequeno em vez de bater a rota
100+ vezes."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from src.presentation.api.v1 import dependencies as deps


def _payload(slug: str) -> dict[str, str]:
    return {
        "slug": slug,
        "trade_name": "Burger House",
        "legal_name": "Burger House Ltda",
        "cnpj": "12.345.678/0001-90",
        "phone": "(11) 99999-8888",
    }


def test_public_route_blocks_after_max_requests(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(deps.settings, "public_rate_limit_max_requests", 3)

    for i in range(3):
        allowed = client.post("/api/v1/restaurants", json=_payload(f"burger-house-{i}"))
        assert allowed.status_code == 201, allowed.text

    blocked = client.post("/api/v1/restaurants", json=_payload("burger-house-blocked"))

    assert blocked.status_code == 429
    body = blocked.json()
    assert body["code"] == "RATE_LIMIT_EXCEEDED"
    assert body["errors"]["retry_after_seconds"] == deps.settings.public_rate_limit_window_seconds


def test_public_route_rate_limit_bucket_is_independent_per_path(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Esgotar o balde de `POST /restaurants` não afeta `GET /by-slug/`
    (mesmo IP, path diferente — mesmo padrão de baldes por rota já usado
    no rate limit de login do `auth-service`)."""
    monkeypatch.setattr(deps.settings, "public_rate_limit_max_requests", 1)
    client.post("/api/v1/restaurants", json=_payload("burger-house"))

    blocked = client.post("/api/v1/restaurants", json=_payload("burger-house-2"))
    assert blocked.status_code == 429

    still_allowed = client.get("/api/v1/restaurants/by-slug/burger-house")
    assert still_allowed.status_code == 200, still_allowed.text
