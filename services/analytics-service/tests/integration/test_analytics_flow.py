"""Testes de integração do `analytics-service`: HTTP real + SQLAlchemy (SQLite).

`AuditLog` só nasce via evento consumido — os testes de HTTP semeiam linhas
diretamente no banco (ver `test_audit_log_handler.py` para o consumo real).
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest_asyncio
from fastapi.testclient import TestClient
from restaurant_core.ids import generate_uuid7
from restaurant_security.jwt import create_access_token
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from src.infrastructure.models.audit_log_model import AuditLogModel

SECRET = "integration-test-secret-key-32chars"


def _headers(tenant_id: uuid.UUID, role: str = "MANAGER") -> dict[str, str]:
    token = create_access_token(str(uuid.uuid4()), str(tenant_id), role, SECRET)
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def seeded_logs(
    sqlite_session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[uuid.UUID, None]:
    tenant_id = uuid.uuid4()
    async with sqlite_session_factory() as session:
        for event_type in ("order.created", "order.created", "notification.requested"):
            session.add(
                AuditLogModel(
                    id=generate_uuid7(),
                    tenant_id=tenant_id,
                    event_id=uuid.uuid4(),
                    event_type=event_type,
                    payload={},
                )
            )
        await session.commit()
    yield tenant_id


def test_list_audit_logs_requires_manager_role(client: TestClient, seeded_logs: uuid.UUID) -> None:
    response = client.get(
        "/api/v1/analytics/audit-logs", headers=_headers(seeded_logs, role="WAITER")
    )
    assert response.status_code == 403


def test_list_audit_logs_returns_paginated_response(
    client: TestClient, seeded_logs: uuid.UUID
) -> None:
    response = client.get("/api/v1/analytics/audit-logs", headers=_headers(seeded_logs))

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert len(body["items"]) == 3
    assert body["limit"] == 50
    assert body["offset"] == 0


def test_list_audit_logs_filters_by_event_type(client: TestClient, seeded_logs: uuid.UUID) -> None:
    response = client.get(
        "/api/v1/analytics/audit-logs",
        params={"event_type": "notification.requested"},
        headers=_headers(seeded_logs),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["event_type"] == "notification.requested"


def test_audit_logs_never_leak_across_tenants(client: TestClient, seeded_logs: uuid.UUID) -> None:
    other_tenant = uuid.uuid4()
    response = client.get("/api/v1/analytics/audit-logs", headers=_headers(other_tenant))

    assert response.status_code == 200
    assert response.json()["total"] == 0


def test_health_check(client: TestClient) -> None:
    response = client.get("/api/v1/analytics/health/check")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
