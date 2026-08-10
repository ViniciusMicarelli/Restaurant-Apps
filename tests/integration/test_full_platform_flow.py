"""Teste de integração ponta-a-ponta contra o `docker-compose.dev.yml` real.

Fluxo (docs/README do plano de implementação, Fase 6): cria restaurante →
cadastra dono → login → cria mesa → cadastra produto → cria pedido → aguarda
a Saga popular o KDS → abre caixa → paga o pedido.

Requer a stack de dev no ar:
    docker compose --env-file .env.dev -f infra/docker/docker-compose.dev.yml up -d

Uso:
    uv run pytest tests/integration -q
"""

from __future__ import annotations

import os
import time
import uuid

import httpx
import pytest

AUTH_URL = os.environ.get("AUTH_SERVICE_URL", "http://localhost:8000")
RESTAURANT_URL = os.environ.get("RESTAURANT_SERVICE_URL", "http://localhost:8001")
MENU_URL = os.environ.get("MENU_SERVICE_URL", "http://localhost:8002")
DINING_URL = os.environ.get("DINING_SERVICE_URL", "http://localhost:8003")
KITCHEN_URL = os.environ.get("KITCHEN_SERVICE_URL", "http://localhost:8004")
ORDER_URL = os.environ.get("ORDER_SERVICE_URL", "http://localhost:8005")
PAYMENT_URL = os.environ.get("PAYMENT_SERVICE_URL", "http://localhost:8007")

_TIMEOUT = httpx.Timeout(10.0)


def _require_stack_up() -> None:
    try:
        httpx.get(f"{AUTH_URL}/api/v1/auth/health", timeout=2.0)
    except httpx.ConnectError:
        pytest.skip(
            "docker-compose.dev.yml não está no ar — suba a stack antes de rodar "
            "este teste (ver docstring do módulo)."
        )


@pytest.fixture(scope="module", autouse=True)
def _ensure_stack_is_reachable() -> None:
    _require_stack_up()


@pytest.fixture(scope="module")
def client() -> httpx.Client:
    with httpx.Client(timeout=_TIMEOUT) as client:
        yield client


def test_full_platform_flow(client: httpx.Client) -> None:
    unique = uuid.uuid4().hex[:10]

    # 1) Cria o restaurante (bootstrap do tenant) — restaurant-service.
    restaurant_response = client.post(
        f"{RESTAURANT_URL}/api/v1/restaurants",
        json={
            "slug": f"e2e-{unique}",
            "trade_name": "Restaurante E2E",
            "legal_name": "Restaurante E2E LTDA",
            "cnpj": "12345678000199",
            "phone": "11999999999",
            "currency": "BRL",
            "service_fee_percent": 10.0,
        },
    )
    assert restaurant_response.status_code == 201, restaurant_response.text
    tenant_id = restaurant_response.json()["id"]

    # 2) Cadastra o dono do tenant — auth-service.
    # Domínio gerado dinamicamente (em vez de "e2e.test"/"example.com"): o
    # validador de e-mail do Pydantic rejeita TLDs/domínios reservados
    # (RFC 2606) como "special-use", mesmo em ambiente de teste.
    owner_email = f"owner-{unique}@{unique}.com"
    register_response = client.post(
        f"{AUTH_URL}/api/v1/auth/register-owner",
        json={
            "tenant_id": tenant_id,
            "email": owner_email,
            "password": "senha-segura-123",
            "name": "Dono E2E",
        },
    )
    assert register_response.status_code == 201, register_response.text

    # 3) Login — obtém o access token do dono.
    login_response = client.post(
        f"{AUTH_URL}/api/v1/auth/login",
        json={"email": owner_email, "password": "senha-segura-123"},
    )
    assert login_response.status_code == 200, login_response.text
    access_token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # 4) Cria uma mesa — dining-service.
    table_response = client.post(
        f"{DINING_URL}/api/v1/dining/tables",
        json={"number": 1, "capacity": 4, "qr_code_url": ""},
        headers=headers,
    )
    assert table_response.status_code == 201, table_response.text

    # 5) Cadastra categoria + produto — menu-service.
    category_response = client.post(
        f"{MENU_URL}/api/v1/menu/categories",
        json={"name": "Lanches", "display_order": 0},
        headers=headers,
    )
    assert category_response.status_code == 201, category_response.text
    category_id = category_response.json()["id"]

    product_response = client.post(
        f"{MENU_URL}/api/v1/menu/products",
        json={
            "category_id": category_id,
            "name": "X-Burger E2E",
            "description": "Hambúrguer de teste",
            "price": 25.0,
            "cost_price": 10.0,
            "tax_rate": 0.0,
            "photo_url": "",
            "display_order": 0,
        },
        headers=headers,
    )
    assert product_response.status_code == 201, product_response.text
    product = product_response.json()

    # 6) Cria o pedido — order-service (dispara a Saga `order.created`).
    order_response = client.post(
        f"{ORDER_URL}/api/v1/orders",
        json={
            "order_type": "TABLE",
            "table_number": 1,
            "items": [
                {
                    "product_id": product["id"],
                    "product_name": product["name"],
                    "unit_price": product["price"],
                    "quantity": 2,
                }
            ],
        },
        headers={"X-Tenant-Id": tenant_id},
    )
    assert order_response.status_code == 201, order_response.text
    order = order_response.json()
    assert order["total_amount"] == 50.0

    # 7) Aguarda a Saga: kitchen-service consome `order.created` via RabbitMQ
    # e popula o KDS — poll com retentativas (processamento assíncrono).
    kds_items = []
    for _ in range(10):
        kds_response = client.get(f"{KITCHEN_URL}/api/v1/kitchen/kds/items", headers=headers)
        assert kds_response.status_code == 200, kds_response.text
        kds_items = [item for item in kds_response.json() if item["order_id"] == order["id"]]
        if kds_items:
            break
        time.sleep(1)

    assert kds_items, "Itens do pedido não apareceram no KDS — Saga (order.created) falhou."
    assert len(kds_items) == 1
    assert kds_items[0]["quantity"] == 2

    # 8) Abre o caixa e paga o pedido — payment-service.
    cash_register_response = client.post(
        f"{PAYMENT_URL}/api/v1/payments/cash-registers",
        json={"operator_id": str(uuid.uuid4()), "opening_amount": 100.0},
        headers=headers,
    )
    assert cash_register_response.status_code == 201, cash_register_response.text
    cash_register_id = cash_register_response.json()["id"]

    payment_response = client.post(
        f"{PAYMENT_URL}/api/v1/payments",
        json={
            "order_id": order["id"],
            "cash_register_id": cash_register_id,
            "expected_total": order["total_amount"],
            "splits": [{"payment_method": "PIX", "amount": order["total_amount"]}],
        },
        headers=headers,
    )
    assert payment_response.status_code == 201, payment_response.text
    assert payment_response.json()["status"] == "APPROVED"
