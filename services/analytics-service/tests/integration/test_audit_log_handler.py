"""Teste de integração do handler curinga de auditoria (`#`) — Saga por coreografia.

Usa um `DatabaseManager` próprio (SQLite em memória) — não depende do
FastAPI nem do RabbitMQ real, apenas do contrato `EventBus`/`DomainEvent`.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from restaurant_database import DatabaseManager
from restaurant_database.base import BaseDBModel
from restaurant_events import DomainEvent
from src.infrastructure.events.audit_log_handler import build_audit_log_handler
from src.infrastructure.repositories.sqlalchemy_audit_log_repository import (
    SQLAlchemyAuditLogRepository,
)


@pytest_asyncio.fixture
async def db_manager() -> AsyncGenerator[DatabaseManager, None]:
    manager = DatabaseManager("sqlite+aiosqlite:///:memory:")
    async with manager.engine.begin() as conn:
        await conn.run_sync(BaseDBModel.metadata.create_all)
    yield manager
    await manager.close()


@pytest.mark.asyncio
async def test_handler_persists_any_event_type(db_manager: DatabaseManager) -> None:
    tenant_id = uuid.uuid4()
    handler = build_audit_log_handler(db_manager)

    await handler(
        DomainEvent(event_type="order.created", tenant_id=tenant_id, payload={"order_id": "abc"})
    )
    await handler(
        DomainEvent(
            event_type="notification.requested", tenant_id=tenant_id, payload={"recipient": "x"}
        )
    )

    async with db_manager.session() as session:
        logs, total = await SQLAlchemyAuditLogRepository(session, tenant_id).list_paginated(
            limit=50, offset=0
        )

    assert total == 2
    assert {log.event_type for log in logs} == {"order.created", "notification.requested"}


@pytest.mark.asyncio
async def test_handler_is_idempotent_on_redelivery(db_manager: DatabaseManager) -> None:
    tenant_id = uuid.uuid4()
    handler = build_audit_log_handler(db_manager)
    event = DomainEvent(event_type="order.created", tenant_id=tenant_id, payload={})

    await handler(event)
    await handler(event)  # reentrega simulada pelo broker

    async with db_manager.session() as session:
        _logs, total = await SQLAlchemyAuditLogRepository(session, tenant_id).list_paginated(
            limit=50, offset=0
        )

    assert total == 1
