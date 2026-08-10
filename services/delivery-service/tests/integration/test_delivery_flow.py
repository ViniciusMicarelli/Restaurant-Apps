"""Testes de integração do `delivery-service`: HTTP real + SQLAlchemy (SQLite)."""

from __future__ import annotations

import uuid
from typing import Any, cast

from fastapi.testclient import TestClient
from restaurant_security.jwt import create_access_token

SECRET = "integration-test-secret-key-32chars"


def _headers(tenant_id: uuid.UUID, role: str = "WAITER") -> dict[str, str]:
    token = create_access_token(str(uuid.uuid4()), str(tenant_id), role, SECRET)
    return {"Authorization": f"Bearer {token}"}


def _create_delivery(client: TestClient, tenant_id: uuid.UUID) -> dict[str, Any]:
    response = client.post(
        "/api/v1/deliveries",
        json={"order_id": str(uuid.uuid4()), "delivery_address": "Rua das Flores, 123"},
        headers=_headers(tenant_id),
    )
    assert response.status_code == 201, response.text
    return cast("dict[str, Any]", response.json())


def test_create_delivery_requires_authentication(client: TestClient) -> None:
    response = client.post(
        "/api/v1/deliveries",
        json={"order_id": str(uuid.uuid4()), "delivery_address": "Rua X"},
    )
    assert response.status_code == 401


def test_create_and_list_deliveries(client: TestClient) -> None:
    tenant_id = uuid.uuid4()
    _create_delivery(client, tenant_id)

    response = client.get("/api/v1/deliveries", headers=_headers(tenant_id))

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_deliveries_never_leak_across_tenants(client: TestClient) -> None:
    tenant_a, tenant_b = uuid.uuid4(), uuid.uuid4()
    _create_delivery(client, tenant_a)

    response = client.get("/api/v1/deliveries", headers=_headers(tenant_b))

    assert response.status_code == 200
    assert response.json() == []


def test_assign_courier_and_update_status_flow(client: TestClient) -> None:
    tenant_id = uuid.uuid4()
    delivery = _create_delivery(client, tenant_id)

    assign_response = client.post(
        f"/api/v1/deliveries/{delivery['id']}/assign-courier",
        json={"courier_name": "João Motoboy"},
        headers=_headers(tenant_id),
    )
    assert assign_response.status_code == 200
    assert assign_response.json()["status"] == "ASSIGNED"

    status_response = client.patch(
        f"/api/v1/deliveries/{delivery['id']}/status",
        json={"new_status": "IN_TRANSIT"},
        headers=_headers(tenant_id),
    )
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "IN_TRANSIT"


def test_update_status_invalid_transition_returns_conflict(client: TestClient) -> None:
    tenant_id = uuid.uuid4()
    delivery = _create_delivery(client, tenant_id)

    response = client.patch(
        f"/api/v1/deliveries/{delivery['id']}/status",
        json={"new_status": "DELIVERED"},
        headers=_headers(tenant_id),
    )

    assert response.status_code == 409


def test_health_check(client: TestClient) -> None:
    response = client.get("/api/v1/deliveries/health/check")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
