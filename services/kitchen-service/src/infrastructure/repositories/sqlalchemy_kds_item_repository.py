"""Implementação concreta de `KDSItemRepositoryInterface` sobre SQLAlchemy 2.0 Async."""

from __future__ import annotations

import uuid

from restaurant_database import SQLAlchemyRepository
from sqlalchemy import select
from src.domain.entities.kds_item import KDSItem, KDSStation
from src.infrastructure.models.kds_item_model import KDSItemModel


def _to_entity(model: KDSItemModel) -> KDSItem:
    return KDSItem(
        id=model.id,
        tenant_id=model.tenant_id,
        order_id=model.order_id,
        product_id=model.product_id,
        product_name=model.product_name,
        quantity=model.quantity,
        station=model.station,
        table_number=model.table_number,
        notes=model.notes,
        status=model.status,
        created_at=model.created_at,
        ready_at=model.ready_at,
        delivered_at=model.delivered_at,
    )


class SQLAlchemyKDSItemRepository(SQLAlchemyRepository[KDSItemModel]):
    model = KDSItemModel

    async def get_by_id(self, kds_item_id: uuid.UUID) -> KDSItem | None:
        model = await super().get_model_by_id(kds_item_id)
        return _to_entity(model) if model is not None else None

    async def list_all(self, *, station: KDSStation | None = None) -> list[KDSItem]:
        stmt = (
            select(self.model)
            .where(self.model.tenant_id == self._tenant_id, self.model.deleted_at.is_(None))
            .order_by(self.model.created_at.asc())
        )
        if station is not None:
            stmt = stmt.where(self.model.station == station)
        result = await self._session.execute(stmt)
        return [_to_entity(m) for m in result.scalars().all()]

    async def add(self, item: KDSItem) -> KDSItem:
        model = KDSItemModel(
            id=item.id,
            tenant_id=item.tenant_id,
            order_id=item.order_id,
            product_id=item.product_id,
            product_name=item.product_name,
            quantity=item.quantity,
            station=item.station,
            table_number=item.table_number,
            notes=item.notes,
            status=item.status,
        )
        created = await super().add_model(model)
        return _to_entity(created)

    async def save(self, item: KDSItem) -> KDSItem:
        model = await self._session.get(KDSItemModel, item.id)
        if model is None:
            msg = f"Item do KDS '{item.id}' não encontrado para atualização."
            raise LookupError(msg)
        model.status = item.status
        model.station = item.station
        model.ready_at = item.ready_at
        model.delivered_at = item.delivered_at
        saved = await super().save_model(model)
        return _to_entity(saved)
