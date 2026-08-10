"""Caso de uso: registro de um evento de domínio consumido como entrada imutável de auditoria.

Idempotente por `event_id`: se o mesmo evento já foi registrado (reentrega
pelo broker), a segunda tentativa é ignorada silenciosamente em vez de
duplicar o registro de auditoria.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from restaurant_core.ids import generate_uuid7
from src.application.interfaces.repository_interface import AuditLogRepositoryInterface
from src.domain.entities.audit_log import AuditLog


@dataclass
class RecordAuditLogUseCase:
    audit_log_repository: AuditLogRepositoryInterface

    async def execute(
        self,
        *,
        tenant_id: uuid.UUID,
        event_id: uuid.UUID,
        event_type: str,
        payload: dict[str, Any],
        occurred_at: datetime,
    ) -> None:
        if await self.audit_log_repository.exists_by_event_id(event_id):
            return

        log = AuditLog(
            id=generate_uuid7(),
            tenant_id=tenant_id,
            event_id=event_id,
            event_type=event_type,
            payload=payload,
            occurred_at=occurred_at,
        )
        await self.audit_log_repository.add(log)
