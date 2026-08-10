"""Contratos de repositório do serviço de Analytics & Auditoria."""

from __future__ import annotations

import uuid
from typing import Protocol

from src.domain.entities.audit_log import AuditLog


class AuditLogRepositoryInterface(Protocol):
    """Append-only — nenhum método de atualização/remoção é exposto (auditoria imutável)."""

    async def add(self, log: AuditLog) -> AuditLog: ...

    async def exists_by_event_id(self, event_id: uuid.UUID) -> bool: ...

    async def list_paginated(
        self, *, limit: int, offset: int, event_type: str | None = None
    ) -> tuple[list[AuditLog], int]:
        """Retorna a página de resultados e o total de registros (sem paginação)."""
        ...
