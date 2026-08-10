"""Testes de integração do `kitchen-service`: HTTP real + SQLAlchemy (SQLite)."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest_asyncio
from fastapi.testclient import TestClient
from restaurant_security.jwt import create_access_token
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from src.domain.entities.kds_item import KDSItemStatus, KDSStation
from src.infrastructure.models.kds_item_model import KDSItemModel

SECRET = "integration-test-secret-key-32chars"


def _kitchen_headers(tenant_id: uuid.UUID, role: str = "KITCHEN_STAFF") -> dict[str, str]:
    token = create_access_token(str(uuid.uuid4()), str(tenant_id), role, SECRET)
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def seeded_item(
    sqlite_session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[tuple[uuid.UUID, uuid.UUID], None]:
    """Insere um `KDSItem` diretamente no banco (itens só nascem via evento `order.created`)."""
    tenant_id = uuid.uuid4()
    item_id = uuid.uuid4()
    async with sqlite_session_factory() as session:
        session.add(
            KDSItemModel(
                id=item_id,
                tenant_id=tenant_id,
                order_id=uuid.uuid4(),
                product_id=uuid.uuid4(),
                product_name="X-Burger",
                quantity=2,
                station=KDSStation.COZINHA_QUENTE,
                table_number=5,
                status=KDSItemStatus.PENDING,
            )
        )
        await session.commit()
    yield tenant_id, item_id


def test_list_kds_items_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/kitchen/kds/items")
    assert response.status_code == 401


def test_list_kds_items_returns_seeded_item(
    client: TestClient, seeded_item: tuple[uuid.UUID, uuid.UUID]
) -> None:
    tenant_id, item_id = seeded_item
    response = client.get("/api/v1/kitchen/kds/items", headers=_kitchen_headers(tenant_id))

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == str(item_id)
    assert body[0]["status"] == "PENDING"


def test_list_kds_items_filters_by_station(
    client: TestClient, seeded_item: tuple[uuid.UUID, uuid.UUID]
) -> None:
    tenant_id, _item_id = seeded_item
    response = client.get(
        "/api/v1/kitchen/kds/items",
        params={"station": "BAR"},
        headers=_kitchen_headers(tenant_id),
    )

    assert response.status_code == 200
    assert response.json() == []


def test_kds_items_never_leak_across_tenants(
    client: TestClient, seeded_item: tuple[uuid.UUID, uuid.UUID]
) -> None:
    other_tenant = uuid.uuid4()
    response = client.get("/api/v1/kitchen/kds/items", headers=_kitchen_headers(other_tenant))

    assert response.status_code == 200
    assert response.json() == []


def test_update_status_requires_kitchen_role(
    client: TestClient, seeded_item: tuple[uuid.UUID, uuid.UUID]
) -> None:
    tenant_id, item_id = seeded_item
    response = client.patch(
        f"/api/v1/kitchen/kds/items/{item_id}/status",
        json={"new_status": "PREPARING"},
        headers=_kitchen_headers(tenant_id, role="WAITER"),
    )

    assert response.status_code == 403


def test_update_status_flow_broadcasts_change(
    client: TestClient, seeded_item: tuple[uuid.UUID, uuid.UUID], broadcaster: object
) -> None:
    tenant_id, item_id = seeded_item
    response = client.patch(
        f"/api/v1/kitchen/kds/items/{item_id}/status",
        json={"new_status": "PREPARING"},
        headers=_kitchen_headers(tenant_id),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "PREPARING"
    assert len(broadcaster.messages) == 1  # type: ignore[attr-defined]
    assert broadcaster.messages[0][1]["event"] == "KDS_ITEM_STATUS_CHANGED"  # type: ignore[attr-defined]


def test_update_status_invalid_transition_returns_conflict(
    client: TestClient, seeded_item: tuple[uuid.UUID, uuid.UUID]
) -> None:
    tenant_id, item_id = seeded_item
    response = client.patch(
        f"/api/v1/kitchen/kds/items/{item_id}/status",
        json={"new_status": "READY"},
        headers=_kitchen_headers(tenant_id),
    )

    assert response.status_code == 409


def test_update_status_not_found_returns_404(client: TestClient) -> None:
    response = client.patch(
        f"/api/v1/kitchen/kds/items/{uuid.uuid4()}/status",
        json={"new_status": "PREPARING"},
        headers=_kitchen_headers(uuid.uuid4()),
    )

    assert response.status_code == 404


def test_update_status_rejects_extra_fields(
    client: TestClient, seeded_item: tuple[uuid.UUID, uuid.UUID]
) -> None:
    tenant_id, item_id = seeded_item
    response = client.patch(
        f"/api/v1/kitchen/kds/items/{item_id}/status",
        json={"new_status": "PREPARING", "unexpected": "field"},
        headers=_kitchen_headers(tenant_id),
    )

    assert response.status_code == 422


def test_health_check(client: TestClient) -> None:
    response = client.get("/api/v1/kitchen/health/check")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
