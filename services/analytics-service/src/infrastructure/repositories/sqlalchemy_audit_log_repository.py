"""Implementação concreta de `AuditLogRepositoryInterface` sobre SQLAlchemy 2.0 Async.

`AuditLog` é append-only: `occurred_at` reaproveita a coluna `created_at` da
`TenantAwareModel` (é o único carimbo de tempo relevante para uma entrada de
auditoria — não há conceito de "atualização").
"""

from __future__ import annotations

import uuid

from restaurant_database import SQLAlchemyRepository
from sqlalchemy import func, select
from src.domain.entities.audit_log import AuditLog
from src.infrastructure.models.audit_log_model import AuditLogModel


def _to_entity(model: AuditLogModel) -> AuditLog:
    return AuditLog(
        id=model.id,
        tenant_id=model.tenant_id,
        event_id=model.event_id,
        event_type=model.event_type,
        payload=dict(model.payload),
        occurred_at=model.created_at,
    )


class SQLAlchemyAuditLogRepository(SQLAlchemyRepository[AuditLogModel]):
    model = AuditLogModel

    async def add(self, log: AuditLog) -> AuditLog:
        model = AuditLogModel(
            id=log.id,
            tenant_id=log.tenant_id,
            event_id=log.event_id,
            event_type=log.event_type,
            payload=log.payload,
            created_at=log.occurred_at,
        )
        created = await super().add_model(model)
        return _to_entity(created)

    async def exists_by_event_id(self, event_id: uuid.UUID) -> bool:
        stmt = select(self.model.id).where(
            self.model.event_id == event_id, self.model.tenant_id == self._tenant_id
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def list_paginated(
        self, *, limit: int, offset: int, event_type: str | None = None
    ) -> tuple[list[AuditLog], int]:
        filters = [self.model.tenant_id == self._tenant_id, self.model.deleted_at.is_(None)]
        if event_type:
            filters.append(self.model.event_type == event_type)

        count_stmt = select(func.count()).select_from(self.model).where(*filters)
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = (
            select(self.model)
            .where(*filters)
            .order_by(self.model.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        logs = [_to_entity(m) for m in result.scalars().all()]
        return logs, total
