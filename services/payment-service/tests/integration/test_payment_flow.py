"""Testes de integração do `payment-service`: HTTP real + SQLAlchemy (SQLite)."""

from __future__ import annotations

import uuid
from typing import Any, cast

from fastapi.testclient import TestClient
from restaurant_security.jwt import create_access_token
from src.application.interfaces.repository_interface import PayableSummary

SECRET = "integration-test-secret-key-32chars"


def _headers(tenant_id: uuid.UUID, role: str = "CASHIER") -> dict[str, str]:
    token = create_access_token(str(uuid.uuid4()), str(tenant_id), role, SECRET)
    return {"Authorization": f"Bearer {token}"}


def _open_register(client: TestClient, tenant_id: uuid.UUID, **overrides: object) -> dict[str, Any]:
    payload: dict[str, Any] = {"operator_id": str(uuid.uuid4()), "opening_amount": 100.0}
    payload.update(overrides)
    response = client.post(
        "/api/v1/payments/cash-registers", json=payload, headers=_headers(tenant_id)
    )
    assert response.status_code == 201, response.text
    return cast("dict[str, Any]", response.json())


def test_open_cash_register_rejects_role_without_payment_access(client: TestClient) -> None:
    response = client.post(
        "/api/v1/payments/cash-registers",
        json={"operator_id": str(uuid.uuid4()), "opening_amount": 100.0},
        headers=_headers(uuid.uuid4(), role="KITCHEN_STAFF"),
    )
    assert response.status_code == 403


def test_waiter_can_open_own_register_and_process_payment(client: TestClient) -> None:
    """O garçom cobra na mesa com a maquininha (cartão) — precisa abrir o
    próprio caixa e processar o pagamento pra poder fechar a comanda
    (docs/logs/2026-08-06.md)."""
    tenant_id = uuid.uuid4()
    waiter_headers = _headers(tenant_id, role="WAITER")

    open_response = client.post(
        "/api/v1/payments/cash-registers",
        json={"operator_id": str(uuid.uuid4()), "opening_amount": 0.0},
        headers=waiter_headers,
    )
    assert open_response.status_code == 201
    register = open_response.json()

    payment_response = client.post(
        "/api/v1/payments",
        json={
            "order_id": str(uuid.uuid4()),
            "cash_register_id": register["id"],
            "expected_total": 50.0,
            "splits": [{"payment_method": "CREDIT_CARD", "amount": 50.0}],
        },
        headers=waiter_headers,
    )
    assert payment_response.status_code == 201

    # A auditoria mais ampla (qualquer caixa/pagamento do tenant) continua
    # restrita — o garçom não vê nem o `GET` de um caixa por ID.
    forbidden = client.get(
        f"/api/v1/payments/cash-registers/{register['id']}", headers=waiter_headers
    )
    assert forbidden.status_code == 403


def test_open_and_get_cash_register(client: TestClient) -> None:
    tenant_id = uuid.uuid4()
    register = _open_register(client, tenant_id)

    response = client.get(
        f"/api/v1/payments/cash-registers/{register['id']}", headers=_headers(tenant_id)
    )

    assert response.status_code == 200
    assert response.json()["current_balance"] == 100.0
    assert response.json()["status"] == "OPEN"


def test_cash_registers_never_leak_across_tenants(client: TestClient) -> None:
    tenant_a, tenant_b = uuid.uuid4(), uuid.uuid4()
    register = _open_register(client, tenant_a)

    response = client.get(
        f"/api/v1/payments/cash-registers/{register['id']}", headers=_headers(tenant_b)
    )

    assert response.status_code == 404


def test_register_sangria_requires_reason(client: TestClient) -> None:
    tenant_id = uuid.uuid4()
    register = _open_register(client, tenant_id)

    response = client.post(
        f"/api/v1/payments/cash-registers/{register['id']}/movements",
        json={"movement_type": "SANGRIA", "amount": 20.0},
        headers=_headers(tenant_id),
    )

    assert response.status_code == 409


def test_register_sangria_and_supply_updates_balance(client: TestClient) -> None:
    tenant_id = uuid.uuid4()
    register = _open_register(client, tenant_id)

    client.post(
        f"/api/v1/payments/cash-registers/{register['id']}/movements",
        json={"movement_type": "SUPPLY", "amount": 50.0},
        headers=_headers(tenant_id),
    )
    client.post(
        f"/api/v1/payments/cash-registers/{register['id']}/movements",
        json={"movement_type": "SANGRIA", "amount": 30.0, "reason": "Retirada para o cofre"},
        headers=_headers(tenant_id),
    )

    updated = client.get(
        f"/api/v1/payments/cash-registers/{register['id']}", headers=_headers(tenant_id)
    ).json()
    assert updated["current_balance"] == 120.0  # 100 + 50 - 30

    movements = client.get(
        f"/api/v1/payments/cash-registers/{register['id']}/movements", headers=_headers(tenant_id)
    ).json()
    assert len(movements) == 3  # OPENING_FLOAT + SUPPLY + SANGRIA


def test_process_payment_and_close_register_reports_divergence(client: TestClient) -> None:
    tenant_id = uuid.uuid4()
    register = _open_register(client, tenant_id)

    payment_response = client.post(
        "/api/v1/payments",
        json={
            "order_id": str(uuid.uuid4()),
            "cash_register_id": register["id"],
            "expected_total": 50.0,
            "splits": [{"payment_method": "CASH", "amount": 50.0}],
        },
        headers=_headers(tenant_id),
    )
    assert payment_response.status_code == 201
    assert payment_response.json()["total_amount"] == 50.0

    close_response = client.post(
        f"/api/v1/payments/cash-registers/{register['id']}/close",
        json={"counted_amount": 145.0},
        headers=_headers(tenant_id),
    )

    assert close_response.status_code == 200
    assert close_response.json()["closing_divergence"] == -5.0  # esperado 150, contado 145


def test_process_payment_with_idempotency_key_does_not_duplicate(client: TestClient) -> None:
    tenant_id = uuid.uuid4()
    register = _open_register(client, tenant_id)
    headers = {**_headers(tenant_id), "Idempotency-Key": "test-key-1"}
    payload = {
        "order_id": str(uuid.uuid4()),
        "cash_register_id": register["id"],
        "expected_total": 50.0,
        "splits": [{"payment_method": "CASH", "amount": 50.0}],
    }

    first = client.post("/api/v1/payments", json=payload, headers=headers)
    second = client.post("/api/v1/payments", json=payload, headers=headers)

    assert first.json()["id"] == second.json()["id"]

    updated = client.get(
        f"/api/v1/payments/cash-registers/{register['id']}", headers=_headers(tenant_id)
    ).json()
    assert updated["current_balance"] == 150.0  # só somou uma vez


def test_process_payment_rejects_split_mismatch(client: TestClient) -> None:
    tenant_id = uuid.uuid4()
    register = _open_register(client, tenant_id)

    response = client.post(
        "/api/v1/payments",
        json={
            "order_id": str(uuid.uuid4()),
            "cash_register_id": register["id"],
            "expected_total": 50.0,
            "splits": [{"payment_method": "PIX", "amount": 40.0}],
        },
        headers=_headers(tenant_id),
    )

    assert response.status_code == 422


def test_get_payment(client: TestClient) -> None:
    tenant_id = uuid.uuid4()
    register = _open_register(client, tenant_id)

    created = client.post(
        "/api/v1/payments",
        json={
            "order_id": str(uuid.uuid4()),
            "cash_register_id": register["id"],
            "expected_total": 30.0,
            "splits": [{"payment_method": "PIX", "amount": 30.0}],
        },
        headers=_headers(tenant_id),
    ).json()

    response = client.get(f"/api/v1/payments/{created['id']}", headers=_headers(tenant_id))

    assert response.status_code == 200
    assert response.json()["order_id"] == created["order_id"]


def test_process_payment_rejects_underpaid_command(
    client: TestClient, order_service_client_stub: Any
) -> None:
    """Piso de segurança do fluxo autenticado (2026-08-10): expected_total
    declarado abaixo do total real dos pedidos da comanda é rejeitado."""
    tenant_id = uuid.uuid4()
    register = _open_register(client, tenant_id)
    order_service_client_stub.summary = PayableSummary(
        total_amount=500.0, reference_order_id=uuid.uuid4()
    )

    response = client.post(
        "/api/v1/payments",
        json={
            "order_id": str(uuid.uuid4()),
            "cash_register_id": register["id"],
            "command_id": str(uuid.uuid4()),
            "expected_total": 0.01,
            "splits": [{"payment_method": "PIX", "amount": 0.01}],
        },
        headers=_headers(tenant_id),
    )

    assert response.status_code == 422
    assert response.json()["code"] == "UNDERPAID_COMMAND"


def test_process_payment_persists_and_filters_by_command_id(client: TestClient) -> None:
    """ "Payment por Comanda": pagamento de uma comanda com command_id fica
    rastreável de verdade, e GET /payments?command_id= filtra certo."""
    tenant_id = uuid.uuid4()
    register = _open_register(client, tenant_id)
    command_id = str(uuid.uuid4())

    payment_response = client.post(
        "/api/v1/payments",
        json={
            "order_id": str(uuid.uuid4()),
            "cash_register_id": register["id"],
            "command_id": command_id,
            "expected_total": 50.0,
            "splits": [{"payment_method": "PIX", "amount": 50.0}],
        },
        headers=_headers(tenant_id),
    )
    assert payment_response.status_code == 201, payment_response.text
    assert payment_response.json()["command_id"] == command_id

    # Um segundo pagamento sem command_id não deve aparecer no filtro.
    client.post(
        "/api/v1/payments",
        json={
            "order_id": str(uuid.uuid4()),
            "cash_register_id": register["id"],
            "expected_total": 15.0,
            "splits": [{"payment_method": "PIX", "amount": 15.0}],
        },
        headers=_headers(tenant_id),
    )

    filtered = client.get(f"/api/v1/payments?command_id={command_id}", headers=_headers(tenant_id))
    assert filtered.status_code == 200
    results = filtered.json()
    assert len(results) == 1
    assert results[0]["command_id"] == command_id


def test_customer_checkout_approves_payment_without_cash_register(
    client: TestClient, dining_service_client_stub: Any
) -> None:
    """US-05.4: o cliente paga a própria comanda pelo customer-web, sem JWT
    nem caixa aberto — só a secret de QR Code da mesa (aqui simulada válida
    pelo stub do dining-service). `order_id`/`command_id`/`expected_total`
    não são mais aceitos no corpo (revisão de segurança, 2026-08-10): o
    servidor descobre a comanda e o total reais consultando
    dining-service/order-service/restaurant-service (stubados aqui)."""
    tenant_id = uuid.uuid4()

    response = client.post(
        "/api/v1/payments/customer-checkout",
        json={
            "table_number": 5,
            "secret": "secret-valida",
            "splits": [{"payment_method": "PIX", "amount": 50.0}],
        },
        headers={"X-Tenant-Id": str(tenant_id)},
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["total_amount"] == 50.0
    assert body["cash_register_id"] is None
    assert body["command_id"] == str(dining_service_client_stub.open_command.command_id)
    assert body["status"] == "APPROVED"


def test_customer_checkout_rejects_a_forged_order_id_or_total_in_the_body(
    client: TestClient,
) -> None:
    """`order_id`/`command_id`/`expected_total` são campos desconhecidos
    agora — mandar qualquer um deles é rejeitado (422), não silenciosamente
    ignorado, pra deixar bem claro que o cliente não controla mais isso."""
    response = client.post(
        "/api/v1/payments/customer-checkout",
        json={
            "table_number": 5,
            "secret": "secret-valida",
            "expected_total": 0.01,
            "splits": [{"payment_method": "PIX", "amount": 0.01}],
        },
        headers={"X-Tenant-Id": str(uuid.uuid4())},
    )

    assert response.status_code == 422


def test_customer_checkout_rejects_invalid_table_secret(
    client: TestClient, dining_service_client_stub: Any
) -> None:
    dining_service_client_stub.valid = False

    response = client.post(
        "/api/v1/payments/customer-checkout",
        json={
            "table_number": 5,
            "secret": "secret-errada",
            "splits": [{"payment_method": "PIX", "amount": 50.0}],
        },
        headers={"X-Tenant-Id": str(uuid.uuid4())},
    )

    assert response.status_code == 401


def test_customer_checkout_rejects_cash_split(client: TestClient) -> None:
    response = client.post(
        "/api/v1/payments/customer-checkout",
        json={
            "table_number": 5,
            "secret": "secret-valida",
            "splits": [{"payment_method": "CASH", "amount": 50.0}],
        },
        headers={"X-Tenant-Id": str(uuid.uuid4())},
    )

    assert response.status_code == 409


def test_customer_checkout_rejects_split_that_does_not_match_real_total(
    client: TestClient, order_service_client_stub: Any
) -> None:
    """O ataque que motivou a correção: tentar pagar menos que o total real
    (aqui, R$500 de verdade vs. R$0,01 na parcela) é rejeitado."""
    order_service_client_stub.summary = PayableSummary(
        total_amount=500.0, reference_order_id=uuid.uuid4()
    )

    response = client.post(
        "/api/v1/payments/customer-checkout",
        json={
            "table_number": 5,
            "secret": "secret-valida",
            "splits": [{"payment_method": "PIX", "amount": 0.01}],
        },
        headers={"X-Tenant-Id": str(uuid.uuid4())},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "SPLIT_AMOUNT_MISMATCH"


def test_customer_checkout_requires_tenant_id_header(client: TestClient) -> None:
    response = client.post(
        "/api/v1/payments/customer-checkout",
        json={
            "table_number": 5,
            "secret": "secret-valida",
            "order_id": str(uuid.uuid4()),
            "expected_total": 50.0,
            "splits": [{"payment_method": "PIX", "amount": 50.0}],
        },
    )

    assert response.status_code == 403


def test_health_check(client: TestClient) -> None:
    response = client.get("/api/v1/payments/health/check")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
