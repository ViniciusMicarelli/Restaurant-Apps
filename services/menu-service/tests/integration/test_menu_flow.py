"""Testes de integração do `menu-service`: HTTP real + SQLAlchemy (SQLite) + índice de busca fake."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi.testclient import TestClient
from restaurant_security.jwt import create_access_token

SECRET = "integration-test-secret-key-32chars"


def _manager_headers(tenant_id: uuid.UUID) -> dict[str, str]:
    token = create_access_token(str(uuid.uuid4()), str(tenant_id), "MANAGER", SECRET)
    return {"Authorization": f"Bearer {token}"}


def _tenant_headers(tenant_id: uuid.UUID) -> dict[str, str]:
    return {"X-Tenant-Id": str(tenant_id)}


def _create_category(
    client: TestClient, tenant_id: uuid.UUID, name: str = "Lanches"
) -> dict[str, Any]:
    response = client.post(
        "/api/v1/menu/categories", json={"name": name}, headers=_manager_headers(tenant_id)
    )
    assert response.status_code == 201, response.text
    result: dict[str, Any] = response.json()
    return result


def _create_product(
    client: TestClient, tenant_id: uuid.UUID, category_id: str, name: str = "X-Burger"
) -> dict[str, Any]:
    response = client.post(
        "/api/v1/menu/products",
        json={"category_id": category_id, "name": name, "price": 25.0},
        headers=_manager_headers(tenant_id),
    )
    assert response.status_code == 201, response.text
    result: dict[str, Any] = response.json()
    return result


def test_create_category_requires_manager_role(client: TestClient) -> None:
    response = client.post("/api/v1/menu/categories", json={"name": "Lanches"})

    assert response.status_code == 401


def test_create_and_list_categories(client: TestClient) -> None:
    tenant_id = uuid.uuid4()
    _create_category(client, tenant_id, name="Lanches")

    response = client.get("/api/v1/menu/categories", headers=_tenant_headers(tenant_id))

    assert response.status_code == 200
    assert [c["name"] for c in response.json()] == ["Lanches"]


def test_categories_never_leak_across_tenants(client: TestClient) -> None:
    tenant_a, tenant_b = uuid.uuid4(), uuid.uuid4()
    _create_category(client, tenant_a, name="Lanches do Tenant A")

    response = client.get("/api/v1/menu/categories", headers=_tenant_headers(tenant_b))

    assert response.json() == []


def test_create_product_requires_existing_category(client: TestClient) -> None:
    tenant_id = uuid.uuid4()

    response = client.post(
        "/api/v1/menu/products",
        json={"category_id": str(uuid.uuid4()), "name": "X-Burger", "price": 25.0},
        headers=_manager_headers(tenant_id),
    )

    assert response.status_code == 404


def test_create_and_get_product(client: TestClient) -> None:
    tenant_id = uuid.uuid4()
    category = _create_category(client, tenant_id)
    created = _create_product(client, tenant_id, category["id"])

    response = client.get(
        f"/api/v1/menu/products/{created['id']}", headers=_tenant_headers(tenant_id)
    )

    assert response.status_code == 200
    assert response.json()["name"] == "X-Burger"


def test_list_products_filtered_by_category(client: TestClient) -> None:
    tenant_id = uuid.uuid4()
    category_a = _create_category(client, tenant_id, name="Lanches")
    category_b = _create_category(client, tenant_id, name="Bebidas")
    _create_product(client, tenant_id, category_a["id"], name="X-Burger")
    _create_product(client, tenant_id, category_b["id"], name="Refrigerante")

    response = client.get(
        "/api/v1/menu/products",
        params={"category_id": category_a["id"]},
        headers=_tenant_headers(tenant_id),
    )

    assert response.status_code == 200
    assert [p["name"] for p in response.json()] == ["X-Burger"]


def test_update_product_price(client: TestClient) -> None:
    tenant_id = uuid.uuid4()
    category = _create_category(client, tenant_id)
    created = _create_product(client, tenant_id, category["id"])

    response = client.patch(
        f"/api/v1/menu/products/{created['id']}",
        json={"name": "X-Burger", "description": "Atualizado", "price": 29.9, "is_active": True},
        headers=_manager_headers(tenant_id),
    )

    assert response.status_code == 200
    assert response.json()["price"] == 29.9


def test_search_finds_indexed_product(client: TestClient) -> None:
    tenant_id = uuid.uuid4()
    category = _create_category(client, tenant_id)
    _create_product(client, tenant_id, category["id"], name="X-Burger Especial")

    response = client.get(
        "/api/v1/menu/search", params={"q": "Burger"}, headers=_tenant_headers(tenant_id)
    )

    assert response.status_code == 200
    assert any(r["name"] == "X-Burger Especial" for r in response.json())


def test_search_is_isolated_per_tenant(client: TestClient) -> None:
    tenant_a, tenant_b = uuid.uuid4(), uuid.uuid4()
    category_a = _create_category(client, tenant_a)
    _create_product(client, tenant_a, category_a["id"], name="X-Burger Exclusivo")

    response = client.get(
        "/api/v1/menu/search", params={"q": "Burger"}, headers=_tenant_headers(tenant_b)
    )

    assert response.json() == []


def test_create_and_list_addon_groups(client: TestClient) -> None:
    tenant_id = uuid.uuid4()
    category = _create_category(client, tenant_id)
    product = _create_product(client, tenant_id, category["id"])

    create_response = client.post(
        "/api/v1/menu/addon-groups",
        json={
            "product_id": product["id"],
            "name": "Ponto da carne",
            "min_selections": 1,
            "max_selections": 1,
            "options": [{"name": "Mal passado"}, {"name": "Bem passado", "price_delta": 0}],
        },
        headers=_manager_headers(tenant_id),
    )
    assert create_response.status_code == 201, create_response.text

    list_response = client.get(
        f"/api/v1/menu/products/{product['id']}/addon-groups", headers=_tenant_headers(tenant_id)
    )

    assert list_response.status_code == 200
    assert len(list_response.json()) == 1
    assert len(list_response.json()[0]["options"]) == 2


def test_health_check(client: TestClient) -> None:
    response = client.get("/api/v1/menu/health/check")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
