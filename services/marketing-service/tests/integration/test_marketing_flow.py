"""Testes de integração do `marketing-service`: HTTP real + SQLAlchemy (SQLite)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from fastapi.testclient import TestClient
from restaurant_security.jwt import create_access_token

SECRET = "integration-test-secret-key-32chars"
_NOW = datetime.now(UTC)


def _headers(tenant_id: uuid.UUID, role: str = "MANAGER") -> dict[str, str]:
    token = create_access_token(str(uuid.uuid4()), str(tenant_id), role, SECRET)
    return {"Authorization": f"Bearer {token}"}


def _create_coupon(client: TestClient, tenant_id: uuid.UUID, **overrides: object) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "code": "PROMO10",
        "discount_type": "PERCENTAGE",
        "discount_value": 10.0,
        "valid_from": (_NOW - timedelta(days=1)).isoformat(),
        "valid_until": (_NOW + timedelta(days=1)).isoformat(),
    }
    payload.update(overrides)
    response = client.post("/api/v1/marketing/coupons", json=payload, headers=_headers(tenant_id))
    assert response.status_code == 201, response.text
    return cast("dict[str, Any]", response.json())


def test_create_coupon_requires_manager_role(client: TestClient) -> None:
    response = client.post(
        "/api/v1/marketing/coupons",
        json={
            "code": "X",
            "discount_type": "FIXED",
            "discount_value": 5.0,
            "valid_from": (_NOW - timedelta(days=1)).isoformat(),
            "valid_until": (_NOW + timedelta(days=1)).isoformat(),
        },
        headers=_headers(uuid.uuid4(), role="WAITER"),
    )
    assert response.status_code == 403


def test_create_and_list_coupons(client: TestClient) -> None:
    tenant_id = uuid.uuid4()
    _create_coupon(client, tenant_id)

    response = client.get("/api/v1/marketing/coupons", headers=_headers(tenant_id))

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_coupons_never_leak_across_tenants(client: TestClient) -> None:
    tenant_a, tenant_b = uuid.uuid4(), uuid.uuid4()
    _create_coupon(client, tenant_a)

    response = client.get("/api/v1/marketing/coupons", headers=_headers(tenant_b))

    assert response.status_code == 200
    assert response.json() == []


def test_apply_coupon_flow(client: TestClient) -> None:
    tenant_id = uuid.uuid4()
    _create_coupon(client, tenant_id)

    response = client.post(
        "/api/v1/marketing/coupons/apply",
        json={"code": "promo10", "order_total": 100.0},
        headers=_headers(tenant_id, role="CASHIER"),
    )

    assert response.status_code == 200
    assert response.json()["discount_amount"] == 10.0
    assert response.json()["final_total"] == 90.0


def test_apply_unknown_coupon_returns_404(client: TestClient) -> None:
    tenant_id = uuid.uuid4()
    response = client.post(
        "/api/v1/marketing/coupons/apply",
        json={"code": "NOPE", "order_total": 100.0},
        headers=_headers(tenant_id, role="CASHIER"),
    )
    assert response.status_code == 404


def test_apply_expired_coupon_returns_conflict(client: TestClient) -> None:
    tenant_id = uuid.uuid4()
    _create_coupon(
        client,
        tenant_id,
        code="EXPIRED",
        valid_from=(_NOW - timedelta(days=10)).isoformat(),
        valid_until=(_NOW - timedelta(days=1)).isoformat(),
    )

    response = client.post(
        "/api/v1/marketing/coupons/apply",
        json={"code": "EXPIRED", "order_total": 50.0},
        headers=_headers(tenant_id, role="CASHIER"),
    )

    assert response.status_code == 409


def test_health_check(client: TestClient) -> None:
    response = client.get("/api/v1/marketing/health/check")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
