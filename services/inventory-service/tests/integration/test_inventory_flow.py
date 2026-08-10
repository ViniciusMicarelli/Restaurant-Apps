"""Testes de integração do `inventory-service`: HTTP real + SQLAlchemy (SQLite)."""

from __future__ import annotations

import uuid
from typing import Any, cast

from fastapi.testclient import TestClient
from restaurant_security.jwt import create_access_token

SECRET = "integration-test-secret-key-32chars"


def _headers(tenant_id: uuid.UUID, role: str = "MANAGER") -> dict[str, str]:
    token = create_access_token(str(uuid.uuid4()), str(tenant_id), role, SECRET)
    return {"Authorization": f"Bearer {token}"}


def _create_item(client: TestClient, tenant_id: uuid.UUID, **overrides: object) -> dict[str, Any]:
    payload = {
        "name": "Queijo Cheddar",
        "unit": "KG",
        "initial_quantity": 10.0,
        "minimum_quantity": 2.0,
    }
    payload.update(overrides)
    response = client.post("/api/v1/inventory/items", json=payload, headers=_headers(tenant_id))
    assert response.status_code == 201, response.text
    return cast("dict[str, Any]", response.json())


def test_create_inventory_item_requires_manager_role(client: TestClient) -> None:
    response = client.post(
        "/api/v1/inventory/items",
        json={"name": "Queijo", "unit": "KG"},
        headers=_headers(uuid.uuid4(), role="WAITER"),
    )
    assert response.status_code == 403


def test_create_and_list_inventory_items(client: TestClient) -> None:
    tenant_id = uuid.uuid4()
    _create_item(client, tenant_id)

    response = client.get("/api/v1/inventory/items", headers=_headers(tenant_id))

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["name"] == "Queijo Cheddar"


def test_inventory_items_never_leak_across_tenants(client: TestClient) -> None:
    tenant_a, tenant_b = uuid.uuid4(), uuid.uuid4()
    _create_item(client, tenant_a)

    response = client.get("/api/v1/inventory/items", headers=_headers(tenant_b))

    assert response.status_code == 200
    assert response.json() == []


def test_register_stock_movement_entry_updates_quantity(client: TestClient) -> None:
    tenant_id = uuid.uuid4()
    item = _create_item(client, tenant_id)

    response = client.post(
        f"/api/v1/inventory/items/{item['id']}/movements",
        json={"movement_type": "ENTRY", "quantity": 5.0, "reason": "Compra"},
        headers=_headers(tenant_id),
    )

    assert response.status_code == 200
    assert response.json()["quantity_delta"] == 5.0

    listed = client.get("/api/v1/inventory/items", headers=_headers(tenant_id)).json()
    assert listed[0]["current_quantity"] == 15.0


def test_register_stock_movement_rejects_sale_deduction_type(client: TestClient) -> None:
    tenant_id = uuid.uuid4()
    item = _create_item(client, tenant_id)

    response = client.post(
        f"/api/v1/inventory/items/{item['id']}/movements",
        json={"movement_type": "SALE_DEDUCTION", "quantity": 1.0},
        headers=_headers(tenant_id),
    )

    assert response.status_code == 422


def test_register_stock_movement_loss_exceeding_stock_returns_conflict(client: TestClient) -> None:
    tenant_id = uuid.uuid4()
    item = _create_item(client, tenant_id, initial_quantity=1.0)

    response = client.post(
        f"/api/v1/inventory/items/{item['id']}/movements",
        json={"movement_type": "LOSS", "quantity": 5.0},
        headers=_headers(tenant_id),
    )

    assert response.status_code == 409


def test_adjust_stock_count_sets_quantity_to_counted_value(client: TestClient) -> None:
    tenant_id = uuid.uuid4()
    item = _create_item(client, tenant_id, initial_quantity=10.0)

    response = client.post(
        f"/api/v1/inventory/items/{item['id']}/count",
        json={"counted_quantity": 7.5, "reason": "Contagem mensal"},
        headers=_headers(tenant_id),
    )

    assert response.status_code == 200
    assert response.json()["quantity_delta"] == -2.5


def test_create_and_list_suppliers(client: TestClient) -> None:
    tenant_id = uuid.uuid4()
    create_response = client.post(
        "/api/v1/inventory/suppliers",
        json={"name": "Distribuidora ABC", "contact_phone": None, "contact_email": None},
        headers=_headers(tenant_id),
    )
    assert create_response.status_code == 201

    list_response = client.get("/api/v1/inventory/suppliers", headers=_headers(tenant_id))
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


def test_upsert_and_get_recipe(client: TestClient) -> None:
    tenant_id = uuid.uuid4()
    item = _create_item(client, tenant_id)
    product_id = str(uuid.uuid4())

    upsert_response = client.put(
        "/api/v1/inventory/recipes",
        json={
            "product_id": product_id,
            "items": [{"inventory_item_id": item["id"], "quantity_required": 0.2}],
        },
        headers=_headers(tenant_id),
    )
    assert upsert_response.status_code == 200

    get_response = client.get(
        f"/api/v1/inventory/recipes/{product_id}", headers=_headers(tenant_id)
    )
    assert get_response.status_code == 200
    assert get_response.json()["items"][0]["quantity_required"] == 0.2


def test_get_recipe_not_found_returns_404(client: TestClient) -> None:
    response = client.get(
        f"/api/v1/inventory/recipes/{uuid.uuid4()}", headers=_headers(uuid.uuid4())
    )
    assert response.status_code == 404


def test_health_check(client: TestClient) -> None:
    response = client.get("/api/v1/inventory/health/check")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
