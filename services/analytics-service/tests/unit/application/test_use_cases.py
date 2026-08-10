"""Testes unitários dos casos de uso do `analytics-service` (repositório fake, sem DB real)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from src.application.use_cases.list_audit_logs import ListAuditLogsUseCase
from src.application.use_cases.record_audit_log import RecordAuditLogUseCase
from src.domain.entities.audit_log import AuditLog
from tests.unit.fakes import FakeAuditLogStore


@pytest.mark.asyncio
async def test_record_audit_log_persists_new_event() -> None:
    store = FakeAuditLogStore()
    use_case = RecordAuditLogUseCase(audit_log_repository=store)

    await use_case.execute(
        tenant_id=uuid.uuid4(),
        event_id=uuid.uuid4(),
        event_type="order.created",
        payload={"order_id": "abc"},
        occurred_at=datetime.now(UTC),
    )

    assert len(store.logs) == 1
    assert store.logs[0].event_type == "order.created"


@pytest.mark.asyncio
async def test_record_audit_log_is_idempotent_by_event_id() -> None:
    store = FakeAuditLogStore()
    use_case = RecordAuditLogUseCase(audit_log_repository=store)
    event_id = uuid.uuid4()

    for _ in range(2):
        await use_case.execute(
            tenant_id=uuid.uuid4(),
            event_id=event_id,
            event_type="order.created",
            payload={},
            occurred_at=datetime.now(UTC),
        )

    assert len(store.logs) == 1


@pytest.mark.asyncio
async def test_list_audit_logs_returns_paginated_response() -> None:
    tenant_id = uuid.uuid4()
    logs = [
        AuditLog(
            id=uuid.uuid4(), tenant_id=tenant_id, event_id=uuid.uuid4(), event_type="order.created"
        )
        for _ in range(3)
    ]
    use_case = ListAuditLogsUseCase(audit_log_repository=FakeAuditLogStore(logs))

    result = await use_case.execute(limit=2, offset=0)

    assert result.total == 3
    assert len(result.items) == 2
    assert result.has_more is True


@pytest.mark.asyncio
async def test_list_audit_logs_filters_by_event_type() -> None:
    tenant_id = uuid.uuid4()
    logs = [
        AuditLog(
            id=uuid.uuid4(), tenant_id=tenant_id, event_id=uuid.uuid4(), event_type="order.created"
        ),
        AuditLog(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            event_id=uuid.uuid4(),
            event_type="notification.requested",
        ),
    ]
    use_case = ListAuditLogsUseCase(audit_log_repository=FakeAuditLogStore(logs))

    result = await use_case.execute(limit=50, offset=0, event_type="order.created")

    assert result.total == 1
    assert result.items[0].event_type == "order.created"
