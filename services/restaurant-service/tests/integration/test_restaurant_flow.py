"""Testes de integração do `restaurant-service`: HTTP real + SQLAlchemy (SQLite)."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi.testclient import TestClient
from restaurant_security.jwt import create_access_token

SECRET = "integration-test-secret-key-32chars"


def _create_restaurant(client: TestClient, slug: str = "burger-house") -> dict[str, Any]:
    response = client.post(
        "/api/v1/restaurants",
        json={
            "slug": slug,
            "trade_name": "Burger House",
            "legal_name": "Burger House Ltda",
            "cnpj": "12.345.678/0001-90",
            "phone": "(11) 99999-8888",
        },
    )
    assert response.status_code == 201, response.text
    result: dict[str, Any] = response.json()
    return result


def _owner_headers(tenant_id: str) -> dict[str, str]:
    token = create_access_token(str(uuid.uuid4()), tenant_id, "RESTAURANT_OWNER", SECRET)
    return {"Authorization": f"Bearer {token}"}


def test_create_restaurant_returns_default_branding(client: TestClient) -> None:
    body = _create_restaurant(client)

    assert body["slug"] == "burger-house"
    assert body["currency"] == "BRL"
    assert body["branding"]["primary_color"] == "#EA1D2C"
    assert "--primary-color" in body["branding"]["css_variables"]


def test_create_restaurant_rejects_duplicate_slug(client: TestClient) -> None:
    _create_restaurant(client, slug="burger-house")

    response = client.post(
        "/api/v1/restaurants",
        json={
            "slug": "burger-house",
            "trade_name": "Outro",
            "legal_name": "Outro Ltda",
            "cnpj": "99.888.777/0001-11",
            "phone": "(11) 91111-2222",
        },
    )

    assert response.status_code == 409
    assert response.json()["code"] == "DUPLICATE_SLUG"


def test_create_restaurant_rejects_invalid_slug_format(client: TestClient) -> None:
    response = client.post(
        "/api/v1/restaurants",
        json={
            "slug": "Burger House!!",
            "trade_name": "Burger House",
            "legal_name": "Burger House Ltda",
            "cnpj": "12.345.678/0001-90",
            "phone": "(11) 99999-8888",
        },
    )

    assert response.status_code == 422


def test_get_restaurant_by_slug(client: TestClient) -> None:
    _create_restaurant(client, slug="burger-house")

    response = client.get("/api/v1/restaurants/by-slug/burger-house")

    assert response.status_code == 200
    assert response.json()["trade_name"] == "Burger House"


def test_get_restaurant_by_id(client: TestClient) -> None:
    created = _create_restaurant(client)

    response = client.get(f"/api/v1/restaurants/{created['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_unknown_restaurant_returns_404(client: TestClient) -> None:
    response = client.get(f"/api/v1/restaurants/{uuid.uuid4()}")

    assert response.status_code == 404


def test_owner_can_update_own_restaurant(client: TestClient) -> None:
    created = _create_restaurant(client)

    response = client.patch(
        f"/api/v1/restaurants/{created['id']}",
        json={
            "trade_name": "Burger House Grill",
            "phone": "(11) 90000-0000",
            "currency": "USD",
            "service_fee_percent": 15.0,
        },
        headers=_owner_headers(created["id"]),
    )

    assert response.status_code == 200
    assert response.json()["trade_name"] == "Burger House Grill"
    assert response.json()["currency"] == "USD"


def test_update_without_authentication_returns_401(client: TestClient) -> None:
    created = _create_restaurant(client)

    response = client.patch(
        f"/api/v1/restaurants/{created['id']}",
        json={
            "trade_name": "X",
            "phone": "(11) 90000-0000",
            "currency": "USD",
            "service_fee_percent": 15.0,
        },
    )

    assert response.status_code == 401


def test_owner_cannot_update_a_different_restaurant(client: TestClient) -> None:
    created_a = _create_restaurant(client, slug="burger-house")
    created_b = _create_restaurant(client, slug="pizza-place")

    response = client.patch(
        f"/api/v1/restaurants/{created_b['id']}",
        json={
            "trade_name": "Hostil",
            "phone": "(11) 90000-0000",
            "currency": "USD",
            "service_fee_percent": 15.0,
        },
        headers=_owner_headers(created_a["id"]),
    )

    assert response.status_code == 403


def test_owner_can_update_branding(client: TestClient) -> None:
    created = _create_restaurant(client)

    response = client.put(
        f"/api/v1/restaurants/{created['id']}/branding",
        json={
            "primary_color": "#000000",
            "secondary_color": "#111111",
            "accent_color": "#222222",
            "theme_mode": "dark",
        },
        headers=_owner_headers(created["id"]),
    )

    assert response.status_code == 200
    assert response.json()["branding"]["primary_color"] == "#000000"
    assert response.json()["branding"]["theme_mode"] == "dark"


def test_health_check(client: TestClient) -> None:
    response = client.get("/api/v1/restaurants/health/check")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
