"""Implementação concreta de `TableRepositoryInterface` sobre SQLAlchemy 2.0 Async."""

from __future__ import annotations

import uuid

from restaurant_database import SQLAlchemyRepository
from sqlalchemy import select
from src.domain.entities.table import Table
from src.infrastructure.models.table_model import TableModel


def _to_entity(model: TableModel) -> Table:
    return Table(
        id=model.id,
        tenant_id=model.tenant_id,
        number=model.number,
        capacity=model.capacity,
        status=model.status,
        qr_code_url=model.qr_code_url,
        active_qr_secret=model.active_qr_secret,
        qr_secret_expires_at=model.qr_secret_expires_at,
    )


class SQLAlchemyTableRepository(SQLAlchemyRepository[TableModel]):
    model = TableModel

    async def get_by_id(self, table_id: uuid.UUID) -> Table | None:
        model = await super().get_model_by_id(table_id)
        return _to_entity(model) if model is not None else None

    async def get_by_number(self, number: int) -> Table | None:
        stmt = select(TableModel).where(
            TableModel.tenant_id == self._tenant_id,
            TableModel.number == number,
            TableModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def list_all(self) -> list[Table]:
        models = await super().list_models(limit=1000)
        return [_to_entity(m) for m in models]

    async def add(self, table: Table) -> Table:
        model = TableModel(
            id=table.id,
            tenant_id=table.tenant_id,
            number=table.number,
            capacity=table.capacity,
            status=table.status,
            qr_code_url=table.qr_code_url,
            active_qr_secret=table.active_qr_secret,
            qr_secret_expires_at=table.qr_secret_expires_at,
        )
        created = await super().add_model(model)
        return _to_entity(created)

    async def save(self, table: Table) -> Table:
        model = await self._session.get(TableModel, table.id)
        if model is None:
            msg = f"Mesa '{table.id}' não encontrada para atualização."
            raise LookupError(msg)
        model.status = table.status
        model.capacity = table.capacity
        model.qr_code_url = table.qr_code_url
        model.active_qr_secret = table.active_qr_secret
        model.qr_secret_expires_at = table.qr_secret_expires_at
        saved = await super().save_model(model)
        return _to_entity(saved)
