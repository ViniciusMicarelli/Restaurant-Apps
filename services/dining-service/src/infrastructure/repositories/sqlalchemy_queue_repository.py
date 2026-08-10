"""Implementação concreta de `QueueRepositoryInterface` sobre SQLAlchemy 2.0 Async."""

from __future__ import annotations

import uuid

from restaurant_database import SQLAlchemyRepository
from sqlalchemy import select
from src.domain.entities.queue_entry import QueueEntry, QueueStatus
from src.infrastructure.models.queue_entry_model import QueueEntryModel


def _to_entity(model: QueueEntryModel) -> QueueEntry:
    return QueueEntry(
        id=model.id,
        tenant_id=model.tenant_id,
        customer_name=model.customer_name,
        phone=model.phone,
        party_size=model.party_size,
        status=model.status,
        created_at=model.created_at,
    )


class SQLAlchemyQueueRepository(SQLAlchemyRepository[QueueEntryModel]):
    model = QueueEntryModel

    async def get_by_id(self, entry_id: uuid.UUID) -> QueueEntry | None:
        model = await super().get_model_by_id(entry_id)
        return _to_entity(model) if model is not None else None

    async def list_waiting(self) -> list[QueueEntry]:
        stmt = (
            select(QueueEntryModel)
            .where(
                QueueEntryModel.tenant_id == self._tenant_id,
                QueueEntryModel.status == QueueStatus.WAITING,
                QueueEntryModel.deleted_at.is_(None),
            )
            .order_by(QueueEntryModel.created_at.asc())
        )
        result = await self._session.execute(stmt)
        return [_to_entity(m) for m in result.scalars().all()]

    async def add(self, entry: QueueEntry) -> QueueEntry:
        model = QueueEntryModel(
            id=entry.id,
            tenant_id=entry.tenant_id,
            customer_name=entry.customer_name,
            phone=entry.phone,
            party_size=entry.party_size,
            status=entry.status,
        )
        created = await super().add_model(model)
        return _to_entity(created)

    async def save(self, entry: QueueEntry) -> QueueEntry:
        model = await self._session.get(QueueEntryModel, entry.id)
        if model is None:
            msg = f"Entrada de fila '{entry.id}' não encontrada para atualização."
            raise LookupError(msg)
        model.status = entry.status
        saved = await super().save_model(model)
        return _to_entity(saved)
