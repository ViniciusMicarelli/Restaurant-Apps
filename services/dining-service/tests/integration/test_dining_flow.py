"""Testes de integração do `dining-service`: HTTP real + SQLAlchemy (SQLite)."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi.testclient import TestClient
from restaurant_security.jwt import create_access_token

SECRET = "integration-test-secret-key-32chars"


def _waiter_headers(tenant_id: uuid.UUID, role: str = "WAITER") -> dict[str, str]:
    token = create_access_token(str(uuid.uuid4()), str(tenant_id), role, SECRET)
    return {"Authorization": f"Bearer {token}"}


def _create_table(client: TestClient, tenant_id: uuid.UUID, number: int = 1) -> dict[str, Any]:
    response = client.post(
        "/api/v1/dining/tables",
        json={"number": number, "capacity": 4},
        headers=_waiter_headers(tenant_id, role="MANAGER"),
    )
    assert response.status_code == 201, response.text
    result: dict[str, Any] = response.json()
    return result


def test_create_table_requires_manager_or_owner(client: TestClient) -> None:
    tenant_id = uuid.uuid4()
    response = client.post(
        "/api/v1/dining/tables",
        json={"number": 1, "capacity": 4},
        headers=_waiter_headers(tenant_id),
    )

    assert response.status_code == 403


def test_list_tables_scoped_to_tenant(client: TestClient) -> None:
    tenant_a, tenant_b = uuid.uuid4(), uuid.uuid4()
    _create_table(client, tenant_a, number=1)

    response = client.get("/api/v1/dining/tables", headers=_waiter_headers(tenant_b))

    assert response.status_code == 200
    assert response.json() == []


def test_open_and_close_command_flow(client: TestClient) -> None:
    tenant_id = uuid.uuid4()
    _create_table(client, tenant_id, number=7)

    open_response = client.post(
        "/api/v1/dining/commands/open",
        json={"table_number": 7, "customer_name": "Lucas Oliveira"},
        headers=_waiter_headers(tenant_id),
    )
    assert open_response.status_code == 201, open_response.text
    command = open_response.json()
    assert command["status"] == "OPEN"

    tables = client.get("/api/v1/dining/tables", headers=_waiter_headers(tenant_id)).json()
    assert tables[0]["status"] == "OCCUPIED"

    close_response = client.post(
        f"/api/v1/dining/commands/{command['id']}/close", headers=_waiter_headers(tenant_id)
    )
    assert close_response.status_code == 200
    assert close_response.json()["status"] == "CLOSED"

    tables_after = client.get("/api/v1/dining/tables", headers=_waiter_headers(tenant_id)).json()
    assert tables_after[0]["status"] == "WAITING_CLEANING"

    table_id = tables_after[0]["id"]
    mark_cleaned = client.post(
        f"/api/v1/dining/tables/{table_id}/mark-cleaned", headers=_waiter_headers(tenant_id)
    )
    assert mark_cleaned.status_code == 200, mark_cleaned.text
    assert mark_cleaned.json()["status"] == "AVAILABLE"

    tables_final = client.get("/api/v1/dining/tables", headers=_waiter_headers(tenant_id)).json()
    assert tables_final[0]["status"] == "AVAILABLE"


def test_mark_table_cleaned_rejects_table_not_awaiting_cleaning(client: TestClient) -> None:
    tenant_id = uuid.uuid4()
    table = _create_table(client, tenant_id, number=9)

    response = client.post(
        f"/api/v1/dining/tables/{table['id']}/mark-cleaned", headers=_waiter_headers(tenant_id)
    )

    assert response.status_code == 409


def test_open_command_on_occupied_table_returns_409(client: TestClient) -> None:
    tenant_id = uuid.uuid4()
    _create_table(client, tenant_id, number=7)
    client.post(
        "/api/v1/dining/commands/open",
        json={"table_number": 7, "customer_name": "Lucas"},
        headers=_waiter_headers(tenant_id),
    )

    second_attempt = client.post(
        "/api/v1/dining/commands/open",
        json={"table_number": 7, "customer_name": "Outra Pessoa"},
        headers=_waiter_headers(tenant_id),
    )

    assert second_attempt.status_code == 409


def test_queue_add_list_and_call_next(client: TestClient) -> None:
    tenant_id = uuid.uuid4()
    headers = _waiter_headers(tenant_id)

    add1 = client.post(
        "/api/v1/dining/queue",
        json={"customer_name": "Mariana", "phone": "11999990000", "party_size": 4},
        headers=headers,
    )
    assert add1.status_code == 201
    add2 = client.post(
        "/api/v1/dining/queue",
        json={"customer_name": "Pedro", "phone": "11999990001", "party_size": 2},
        headers=headers,
    )
    assert add2.status_code == 201

    listed = client.get("/api/v1/dining/queue", headers=headers).json()
    assert [e["customer_name"] for e in listed] == ["Mariana", "Pedro"]

    called = client.post("/api/v1/dining/queue/call-next", headers=headers)
    assert called.status_code == 200
    assert called.json()["customer_name"] == "Mariana"

    remaining = client.get("/api/v1/dining/queue", headers=headers).json()
    assert [e["customer_name"] for e in remaining] == ["Pedro"]


def test_get_open_command_for_table_public_endpoint(client: TestClient) -> None:
    """US-05.4: o cliente (sem login) consulta a própria comanda aberta pela
    secret de QR Code — mesmo header público (`X-Tenant-Id`) do cardápio digital."""
    tenant_id = uuid.uuid4()
    table = _create_table(client, tenant_id, number=3)
    client.post(
        "/api/v1/dining/commands/open",
        json={"table_number": 3, "customer_name": "Lucas"},
        headers=_waiter_headers(tenant_id),
    )
    secret = client.post(
        f"/api/v1/dining/tables/{table['id']}/qr-secret/rotate", headers=_waiter_headers(tenant_id)
    ).json()["secret"]

    response = client.get(
        f"/api/v1/dining/tables/3/open-command?secret={secret}",
        headers={"X-Tenant-Id": str(tenant_id)},
    )

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "OPEN"


def test_get_open_command_for_table_rejects_invalid_secret(client: TestClient) -> None:
    tenant_id = uuid.uuid4()
    _create_table(client, tenant_id, number=3)
    client.post(
        "/api/v1/dining/commands/open",
        json={"table_number": 3, "customer_name": "Lucas"},
        headers=_waiter_headers(tenant_id),
    )

    response = client.get(
        "/api/v1/dining/tables/3/open-command?secret=secret-invalida",
        headers={"X-Tenant-Id": str(tenant_id)},
    )

    assert response.status_code == 401


def test_customer_close_command_public_endpoint(client: TestClient) -> None:
    """US-05.4: o cliente fecha a própria comanda pelo autoatendimento,
    liberando a mesa pra limpeza igual ao fechamento feito pelo garçom."""
    tenant_id = uuid.uuid4()
    table = _create_table(client, tenant_id, number=4)
    open_response = client.post(
        "/api/v1/dining/commands/open",
        json={"table_number": 4, "customer_name": "Lucas"},
        headers=_waiter_headers(tenant_id),
    )
    command_id = open_response.json()["id"]
    secret = client.post(
        f"/api/v1/dining/tables/{table['id']}/qr-secret/rotate", headers=_waiter_headers(tenant_id)
    ).json()["secret"]

    response = client.post(
        f"/api/v1/dining/commands/{command_id}/customer-close?secret={secret}",
        headers={"X-Tenant-Id": str(tenant_id)},
    )

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "CLOSED"

    tables_after = client.get("/api/v1/dining/tables", headers=_waiter_headers(tenant_id)).json()
    assert tables_after[0]["status"] == "WAITING_CLEANING"


def test_customer_close_command_rejects_other_tenants_command(client: TestClient) -> None:
    tenant_a, tenant_b = uuid.uuid4(), uuid.uuid4()
    table = _create_table(client, tenant_a, number=5)
    open_response = client.post(
        "/api/v1/dining/commands/open",
        json={"table_number": 5, "customer_name": "Lucas"},
        headers=_waiter_headers(tenant_a),
    )
    command_id = open_response.json()["id"]
    secret = client.post(
        f"/api/v1/dining/tables/{table['id']}/qr-secret/rotate", headers=_waiter_headers(tenant_a)
    ).json()["secret"]

    response = client.post(
        f"/api/v1/dining/commands/{command_id}/customer-close?secret={secret}",
        headers={"X-Tenant-Id": str(tenant_b)},
    )

    assert response.status_code == 404


def test_health_check(client: TestClient) -> None:
    response = client.get("/api/v1/dining/health/check")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
