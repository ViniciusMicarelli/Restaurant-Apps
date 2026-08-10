"""Fake em memória de `AuditLogRepositoryInterface` — usado pelos testes unitários."""

from __future__ import annotations

import uuid

from src.domain.entities.audit_log import AuditLog


class FakeAuditLogStore:
    def __init__(self, logs: list[AuditLog] | None = None) -> None:
        self.logs: list[AuditLog] = list(logs or [])

    async def add(self, log: AuditLog) -> AuditLog:
        self.logs.append(log)
        return log

    async def exists_by_event_id(self, event_id: uuid.UUID) -> bool:
        return any(log.event_id == event_id for log in self.logs)

    async def list_paginated(
        self, *, limit: int, offset: int, event_type: str | None = None
    ) -> tuple[list[AuditLog], int]:
        filtered = [log for log in self.logs if event_type is None or log.event_type == event_type]
        ordered = sorted(filtered, key=lambda log: log.occurred_at, reverse=True)
        return ordered[offset : offset + limit], len(filtered)
