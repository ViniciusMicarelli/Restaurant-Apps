"""Teste de integração do handler do evento `order.created` (Saga por coreografia).

Usa um `DatabaseManager` próprio (SQLite em memória) — não depende do FastAPI
nem do RabbitMQ real, apenas do contrato `EventBus`/`DomainEvent`.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from restaurant_database import DatabaseManager
from restaurant_database.base import BaseDBModel
from restaurant_events import DomainEvent
from src.infrastructure.events.order_created_handler import build_order_created_handler
from src.infrastructure.repositories.sqlalchemy_kds_item_repository import (
    SQLAlchemyKDSItemRepository,
)
from tests.unit.fakes import FakeBroadcaster


@pytest_asyncio.fixture
async def db_manager() -> AsyncGenerator[DatabaseManager, None]:
    manager = DatabaseManager("sqlite+aiosqlite:///:memory:")
    async with manager.engine.begin() as conn:
        await conn.run_sync(BaseDBModel.metadata.create_all)
    yield manager
    await manager.close()


@pytest.mark.asyncio
async def test_order_created_event_creates_one_kds_item_per_order_item(
    db_manager: DatabaseManager,
) -> None:
    broadcaster = FakeBroadcaster()
    handler = build_order_created_handler(db_manager, broadcaster)

    tenant_id, order_id = uuid.uuid4(), uuid.uuid4()
    event = DomainEvent(
        event_type="order.created",
        tenant_id=tenant_id,
        payload={
            "order_id": str(order_id),
            "table_number": 7,
            "items": [
                {"product_id": str(uuid.uuid4()), "product_name": "X-Burger", "quantity": 2},
                {"product_id": str(uuid.uuid4()), "product_name": "Batata Frita", "quantity": 1},
            ],
        },
    )

    await handler(event)

    async with db_manager.session() as session:
        repository = SQLAlchemyKDSItemRepository(session, tenant_id)
        items = await repository.list_all()

    assert len(items) == 2
    assert all(item.order_id == order_id for item in items)
    assert all(item.table_number == 7 for item in items)
    assert len(broadcaster.messages) == 2


@pytest.mark.asyncio
async def test_order_created_event_is_scoped_to_its_tenant(db_manager: DatabaseManager) -> None:
    broadcaster = FakeBroadcaster()
    handler = build_order_created_handler(db_manager, broadcaster)

    tenant_a, tenant_b = uuid.uuid4(), uuid.uuid4()
    event = DomainEvent(
        event_type="order.created",
        tenant_id=tenant_a,
        payload={
            "order_id": str(uuid.uuid4()),
            "table_number": None,
            "items": [{"product_id": str(uuid.uuid4()), "product_name": "Suco", "quantity": 1}],
        },
    )

    await handler(event)

    async with db_manager.session() as session:
        items_for_other_tenant = await SQLAlchemyKDSItemRepository(session, tenant_b).list_all()

    assert items_for_other_tenant == []
