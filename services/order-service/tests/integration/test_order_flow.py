"""Testes de integração do `order-service`: HTTP real + SQLAlchemy (SQLite) + EventBus fake."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi.testclient import TestClient
from restaurant_events import InMemoryEventBus
from restaurant_security.jwt import create_access_token

SECRET = "integration-test-secret-key-32chars"


def _tenant_headers(tenant_id: uuid.UUID) -> dict[str, str]:
    return {"X-Tenant-Id": str(tenant_id)}


def _manager_headers(tenant_id: uuid.UUID, role: str = "MANAGER") -> dict[str, str]:
    token = create_access_token(str(uuid.uuid4()), str(tenant_id), role, SECRET)
    return {"Authorization": f"Bearer {token}"}


def _order_payload() -> dict[str, Any]:
    return {
        "order_type": "TABLE",
        "table_number": 5,
        "items": [
            {
                "product_id": str(uuid.uuid4()),
                "product_name": "X-Burger",
                "unit_price": 25.0,
                "quantity": 2,
            }
        ],
    }


def test_create_order_computes_total(client: TestClient) -> None:
    tenant_id = uuid.uuid4()
    response = client.post(
        "/api/v1/orders", json=_order_payload(), headers=_tenant_headers(tenant_id)
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "PENDING"
    assert body["total_amount"] == 50.0


def test_create_order_publishes_saga_event(client: TestClient, event_bus: InMemoryEventBus) -> None:
    tenant_id = uuid.uuid4()
    response = client.post(
        "/api/v1/orders", json=_order_payload(), headers=_tenant_headers(tenant_id)
    )

    assert len(event_bus.published) == 1
    routing_key, event = event_bus.published[0]
    assert routing_key == "order.created"
    assert event.payload["order_id"] == response.json()["id"]


def test_create_order_with_idempotency_key_does_not_duplicate(client: TestClient) -> None:
    tenant_id = uuid.uuid4()
    headers = {**_tenant_headers(tenant_id), "Idempotency-Key": "test-key-1"}

    first = client.post("/api/v1/orders", json=_order_payload(), headers=headers)
    second = client.post("/api/v1/orders", json=_order_payload(), headers=headers)

    assert first.json()["id"] == second.json()["id"]

    listed = client.get("/api/v1/orders", headers=_tenant_headers(tenant_id)).json()
    assert len(listed) == 1


def test_create_order_requires_at_least_one_item(client: TestClient) -> None:
    tenant_id = uuid.uuid4()
    payload = _order_payload()
    payload["items"] = []

    response = client.post("/api/v1/orders", json=payload, headers=_tenant_headers(tenant_id))

    assert response.status_code == 422


def test_transition_status_requires_staff_role(client: TestClient) -> None:
    tenant_id = uuid.uuid4()
    created = client.post(
        "/api/v1/orders", json=_order_payload(), headers=_tenant_headers(tenant_id)
    ).json()

    response = client.patch(
        f"/api/v1/orders/{created['id']}/status", json={"new_status": "PREPARING"}
    )

    assert response.status_code == 401


def test_transition_status_flow(client: TestClient) -> None:
    tenant_id = uuid.uuid4()
    created = client.post(
        "/api/v1/orders", json=_order_payload(), headers=_tenant_headers(tenant_id)
    ).json()
    headers = _manager_headers(tenant_id, role="KITCHEN_STAFF")

    response = client.patch(
        f"/api/v1/orders/{created['id']}/status", json={"new_status": "PREPARING"}, headers=headers
    )

    assert response.status_code == 200
    assert response.json()["status"] == "PREPARING"


def test_cancel_order_requires_manager_or_owner(client: TestClient) -> None:
    tenant_id = uuid.uuid4()
    created = client.post(
        "/api/v1/orders", json=_order_payload(), headers=_tenant_headers(tenant_id)
    ).json()
    headers = _manager_headers(tenant_id, role="WAITER")

    response = client.post(
        f"/api/v1/orders/{created['id']}/cancel",
        json={"cancellation_reason": "Motivo qualquer"},
        headers=headers,
    )

    assert response.status_code == 403


def test_cancel_order_flow(client: TestClient) -> None:
    tenant_id = uuid.uuid4()
    created = client.post(
        "/api/v1/orders", json=_order_payload(), headers=_tenant_headers(tenant_id)
    ).json()
    headers = _manager_headers(tenant_id)

    response = client.post(
        f"/api/v1/orders/{created['id']}/cancel",
        json={"cancellation_reason": "Cliente desistiu"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "CANCELLED"
    assert response.json()["cancellation_reason"] == "Cliente desistiu"


def test_orders_never_leak_across_tenants(client: TestClient) -> None:
    tenant_a, tenant_b = uuid.uuid4(), uuid.uuid4()
    client.post("/api/v1/orders", json=_order_payload(), headers=_tenant_headers(tenant_a))

    listed_b = client.get("/api/v1/orders", headers=_tenant_headers(tenant_b)).json()

    assert listed_b == []


def test_health_check(client: TestClient) -> None:
    response = client.get("/api/v1/orders/health/check")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
