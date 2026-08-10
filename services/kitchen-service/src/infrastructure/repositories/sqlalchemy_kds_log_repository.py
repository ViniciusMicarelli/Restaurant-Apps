"""Implementação concreta de `KDSLogRepositoryInterface` sobre SQLAlchemy 2.0 Async.

`KDSLog` é append-only (auditoria) — este repositório expõe apenas `add`.
"""

from __future__ import annotations

from restaurant_database import SQLAlchemyRepository
from src.domain.entities.kds_log import KDSLog
from src.infrastructure.models.kds_log_model import KDSLogModel


class SQLAlchemyKDSLogRepository(SQLAlchemyRepository[KDSLogModel]):
    model = KDSLogModel

    async def add(self, log: KDSLog) -> KDSLog:
        model = KDSLogModel(
            id=log.id,
            tenant_id=log.tenant_id,
            kds_item_id=log.kds_item_id,
            from_status=log.from_status,
            to_status=log.to_status,
        )
        created = await super().add_model(model)
        return KDSLog(
            id=created.id,
            tenant_id=created.tenant_id,
            kds_item_id=created.kds_item_id,
            from_status=created.from_status,
            to_status=created.to_status,
            changed_at=created.created_at,
        )
