"""Rate limiting das rotas públicas do autoatendimento do cliente
(docs/SECURITY.md §2.7 — "100 req/min por tenant"). Monkeypatcha o teto
pra um número pequeno em vez de bater a rota 100+ vezes — mesma ideia do
teste de `/login` no `auth-service`, só que aqui a chave é por tenant."""

from __future__ import annotations

import uuid
from typing import Any

import pytest
from fastapi.testclient import TestClient
from restaurant_security.jwt import create_access_token
from src.presentation.api.v1 import dependencies as deps

SECRET = "integration-test-secret-key-32chars"


def _waiter_headers(tenant_id: uuid.UUID, role: str = "MANAGER") -> dict[str, str]:
    token = create_access_token(str(uuid.uuid4()), str(tenant_id), role, SECRET)
    return {"Authorization": f"Bearer {token}"}


def _open_table_with_qr_secret(client: TestClient, tenant_id: uuid.UUID) -> str:
    table_response = client.post(
        "/api/v1/dining/tables",
        json={"number": 9, "capacity": 4},
        headers=_waiter_headers(tenant_id),
    )
    assert table_response.status_code == 201, table_response.text
    table: dict[str, Any] = table_response.json()

    client.post(
        "/api/v1/dining/commands/open",
        json={"table_number": 9, "customer_name": "Lucas"},
        headers=_waiter_headers(tenant_id),
    )
    secret_response = client.post(
        f"/api/v1/dining/tables/{table['id']}/qr-secret/rotate",
        headers=_waiter_headers(tenant_id),
    )
    secret: str = secret_response.json()["secret"]
    return secret


def test_public_route_blocks_after_max_requests(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(deps.settings, "public_rate_limit_max_requests", 3)
    tenant_id = uuid.uuid4()
    secret = _open_table_with_qr_secret(client, tenant_id)
    url = f"/api/v1/dining/tables/9/open-command?secret={secret}"
    headers = {"X-Tenant-Id": str(tenant_id)}

    for _ in range(3):
        allowed = client.get(url, headers=headers)
        assert allowed.status_code == 200, allowed.text

    blocked = client.get(url, headers=headers)

    assert blocked.status_code == 429
    body = blocked.json()
    assert body["code"] == "RATE_LIMIT_EXCEEDED"
    assert body["errors"]["retry_after_seconds"] == deps.settings.public_rate_limit_window_seconds


def test_public_route_rate_limit_bucket_is_independent_per_tenant(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(deps.settings, "public_rate_limit_max_requests", 1)
    tenant_a, tenant_b = uuid.uuid4(), uuid.uuid4()
    secret_a = _open_table_with_qr_secret(client, tenant_a)
    secret_b = _open_table_with_qr_secret(client, tenant_b)

    first = client.get(
        f"/api/v1/dining/tables/9/open-command?secret={secret_a}",
        headers={"X-Tenant-Id": str(tenant_a)},
    )
    assert first.status_code == 200, first.text

    exhausted = client.get(
        f"/api/v1/dining/tables/9/open-command?secret={secret_a}",
        headers={"X-Tenant-Id": str(tenant_a)},
    )
    assert exhausted.status_code == 429

    other_tenant_still_allowed = client.get(
        f"/api/v1/dining/tables/9/open-command?secret={secret_b}",
        headers={"X-Tenant-Id": str(tenant_b)},
    )
    assert other_tenant_still_allowed.status_code == 200, other_tenant_still_allowed.text
