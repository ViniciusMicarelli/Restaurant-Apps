"""Testes de integração do `notification-service`: HTTP real + SQLAlchemy (SQLite) + EventBus fake."""

from __future__ import annotations

import uuid
from typing import Any, cast

from fastapi.testclient import TestClient
from restaurant_events import InMemoryEventBus
from restaurant_security.jwt import create_access_token

SECRET = "integration-test-secret-key-32chars"


def _headers(tenant_id: uuid.UUID, role: str = "MANAGER") -> dict[str, str]:
    token = create_access_token(str(uuid.uuid4()), str(tenant_id), role, SECRET)
    return {"Authorization": f"Bearer {token}"}


def _create_template(
    client: TestClient, tenant_id: uuid.UUID, **overrides: object
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "code": "QUEUE_POSITION",
        "channel": "WHATSAPP",
        "body": "Olá {nome}, sua posição é {posicao}.",
    }
    payload.update(overrides)
    response = client.post(
        "/api/v1/notifications/templates", json=payload, headers=_headers(tenant_id)
    )
    assert response.status_code == 201, response.text
    return cast("dict[str, Any]", response.json())


def test_create_template_requires_manager_role(client: TestClient) -> None:
    response = client.post(
        "/api/v1/notifications/templates",
        json={"code": "X", "channel": "PUSH", "body": "Olá"},
        headers=_headers(uuid.uuid4(), role="WAITER"),
    )
    assert response.status_code == 403


def test_create_email_template_requires_subject(client: TestClient) -> None:
    response = client.post(
        "/api/v1/notifications/templates",
        json={"code": "CONFIRM", "channel": "EMAIL", "body": "Olá {nome}."},
        headers=_headers(uuid.uuid4()),
    )
    assert response.status_code == 422


def test_queue_notification_flow_publishes_event(
    client: TestClient, event_bus: InMemoryEventBus
) -> None:
    tenant_id = uuid.uuid4()
    _create_template(client, tenant_id)

    response = client.post(
        "/api/v1/notifications",
        json={
            "channel": "WHATSAPP",
            "recipient": "+5511999999999",
            "template_code": "queue_position",
            "context": {"nome": "Ana", "posicao": "2"},
        },
        headers=_headers(tenant_id, role="WAITER"),
    )

    assert response.status_code == 201, response.text
    assert response.json()["status"] == "QUEUED"
    assert len(event_bus.published) == 1
    assert event_bus.published[0][0] == "notification.requested"


def test_queue_notification_unknown_template_returns_404(client: TestClient) -> None:
    tenant_id = uuid.uuid4()
    response = client.post(
        "/api/v1/notifications",
        json={
            "channel": "EMAIL",
            "recipient": "a@b.com",
            "template_code": "NOPE",
            "context": {},
        },
        headers=_headers(tenant_id, role="WAITER"),
    )
    assert response.status_code == 404


def test_list_notifications_never_leaks_across_tenants(client: TestClient) -> None:
    tenant_a, tenant_b = uuid.uuid4(), uuid.uuid4()
    _create_template(client, tenant_a)
    client.post(
        "/api/v1/notifications",
        json={
            "channel": "WHATSAPP",
            "recipient": "+5511999999999",
            "template_code": "queue_position",
            "context": {"nome": "Ana", "posicao": "2"},
        },
        headers=_headers(tenant_a, role="WAITER"),
    )

    response = client.get("/api/v1/notifications", headers=_headers(tenant_b, role="WAITER"))

    assert response.status_code == 200
    assert response.json() == []


def test_health_check(client: TestClient) -> None:
    response = client.get("/api/v1/notifications/health/check")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
