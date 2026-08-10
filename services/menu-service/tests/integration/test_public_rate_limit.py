"""Rate limiting das rotas públicas do cardápio digital (docs/SECURITY.md
§2.7 — "100 req/min por tenant"). Monkeypatcha o teto pra um número pequeno
em vez de bater a rota 100+ vezes."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from src.presentation.api.v1 import dependencies as deps
from tests.integration.test_menu_flow import _create_category, _manager_headers, _tenant_headers


def test_public_route_blocks_after_max_requests(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(deps.settings, "public_rate_limit_max_requests", 3)
    tenant_id = uuid.uuid4()
    _create_category(client, tenant_id)
    headers = _tenant_headers(tenant_id)

    for _ in range(3):
        allowed = client.get("/api/v1/menu/categories", headers=headers)
        assert allowed.status_code == 200, allowed.text

    blocked = client.get("/api/v1/menu/categories", headers=headers)

    assert blocked.status_code == 429
    body = blocked.json()
    assert body["code"] == "RATE_LIMIT_EXCEEDED"
    assert body["errors"]["retry_after_seconds"] == deps.settings.public_rate_limit_window_seconds


def test_public_route_rate_limit_bucket_is_independent_per_tenant(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(deps.settings, "public_rate_limit_max_requests", 1)
    tenant_a, tenant_b = uuid.uuid4(), uuid.uuid4()
    _create_category(client, tenant_a)
    _create_category(client, tenant_b)

    first = client.get("/api/v1/menu/categories", headers=_tenant_headers(tenant_a))
    assert first.status_code == 200, first.text

    exhausted = client.get("/api/v1/menu/categories", headers=_tenant_headers(tenant_a))
    assert exhausted.status_code == 429

    other_tenant_still_allowed = client.get(
        "/api/v1/menu/categories", headers=_tenant_headers(tenant_b)
    )
    assert other_tenant_still_allowed.status_code == 200, other_tenant_still_allowed.text


def test_write_routes_are_not_rate_limited_by_public_bucket(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Escritas (Manager/Owner autenticado) não passam por
    `enforce_public_rate_limit` — só as rotas de leitura marcadas como
    públicas no router. Um teto baixo no balde público não deve bloquear
    criação de categorias mesmo com o mesmo tenant."""
    monkeypatch.setattr(deps.settings, "public_rate_limit_max_requests", 1)
    tenant_id = uuid.uuid4()

    for i in range(3):
        response = client.post(
            "/api/v1/menu/categories",
            json={"name": f"Categoria {i}"},
            headers=_manager_headers(tenant_id),
        )
        assert response.status_code == 201, response.text
