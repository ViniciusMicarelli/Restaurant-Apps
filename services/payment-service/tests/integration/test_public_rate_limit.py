"""Rate limiting da rota pública de autoatendimento (docs/SECURITY.md §2.7
— "100 req/min por tenant"). Monkeypatcha o teto pra um número pequeno em
vez de bater a rota 100+ vezes."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from src.presentation.api.v1 import dependencies as deps


def _checkout_payload() -> dict[str, object]:
    return {
        "table_number": 5,
        "secret": "secret-valida",
        "splits": [{"payment_method": "PIX", "amount": 50.0}],
    }


def test_public_route_blocks_after_max_requests(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(deps.settings, "public_rate_limit_max_requests", 3)
    tenant_id = uuid.uuid4()
    headers = {"X-Tenant-Id": str(tenant_id)}

    for _ in range(3):
        allowed = client.post(
            "/api/v1/payments/customer-checkout", json=_checkout_payload(), headers=headers
        )
        assert allowed.status_code == 201, allowed.text

    blocked = client.post(
        "/api/v1/payments/customer-checkout", json=_checkout_payload(), headers=headers
    )

    assert blocked.status_code == 429
    body = blocked.json()
    assert body["code"] == "RATE_LIMIT_EXCEEDED"
    assert body["errors"]["retry_after_seconds"] == deps.settings.public_rate_limit_window_seconds


def test_public_route_rate_limit_bucket_is_independent_per_tenant(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(deps.settings, "public_rate_limit_max_requests", 1)
    tenant_a, tenant_b = uuid.uuid4(), uuid.uuid4()

    first = client.post(
        "/api/v1/payments/customer-checkout",
        json=_checkout_payload(),
        headers={"X-Tenant-Id": str(tenant_a)},
    )
    assert first.status_code == 201, first.text

    exhausted = client.post(
        "/api/v1/payments/customer-checkout",
        json=_checkout_payload(),
        headers={"X-Tenant-Id": str(tenant_a)},
    )
    assert exhausted.status_code == 429

    other_tenant_still_allowed = client.post(
        "/api/v1/payments/customer-checkout",
        json=_checkout_payload(),
        headers={"X-Tenant-Id": str(tenant_b)},
    )
    assert other_tenant_still_allowed.status_code == 201, other_tenant_still_allowed.text
