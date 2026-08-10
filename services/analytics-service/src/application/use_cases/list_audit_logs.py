"""Caso de uso: consulta paginada do log de auditoria."""

from __future__ import annotations

from dataclasses import dataclass

from restaurant_common.pagination import PaginatedResponse
from src.application.dtos.audit_log_dtos import AuditLogResponse
from src.application.interfaces.repository_interface import AuditLogRepositoryInterface
from src.domain.entities.audit_log import AuditLog


def _to_response(log: AuditLog) -> AuditLogResponse:
    return AuditLogResponse(
        id=log.id,
        tenant_id=log.tenant_id,
        event_id=log.event_id,
        event_type=log.event_type,
        payload=log.payload,
        occurred_at=log.occurred_at,
    )


@dataclass
class ListAuditLogsUseCase:
    audit_log_repository: AuditLogRepositoryInterface

    async def execute(
        self, *, limit: int = 50, offset: int = 0, event_type: str | None = None
    ) -> PaginatedResponse[AuditLogResponse]:
        logs, total = await self.audit_log_repository.list_paginated(
            limit=limit, offset=offset, event_type=event_type
        )
        return PaginatedResponse[AuditLogResponse](
            items=[_to_response(log) for log in logs], total=total, limit=limit, offset=offset
        )
