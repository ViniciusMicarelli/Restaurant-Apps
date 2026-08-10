"""Implementação concreta de `StockMovementRepositoryInterface` sobre SQLAlchemy 2.0 Async.

`StockMovement` é append-only (auditoria) — este repositório nunca atualiza
ou remove um registro já criado.
"""

from __future__ import annotations

import uuid

from restaurant_database import SQLAlchemyRepository
from sqlalchemy import select
from src.domain.entities.stock_movement import StockMovement
from src.infrastructure.models.stock_movement_model import StockMovementModel


def _to_entity(model: StockMovementModel) -> StockMovement:
    return StockMovement(
        id=model.id,
        tenant_id=model.tenant_id,
        inventory_item_id=model.inventory_item_id,
        movement_type=model.movement_type,
        quantity_delta=model.quantity_delta,
        reason=model.reason,
        order_id=model.order_id,
        created_at=model.created_at,
    )


class SQLAlchemyStockMovementRepository(SQLAlchemyRepository[StockMovementModel]):
    model = StockMovementModel

    async def add(self, movement: StockMovement) -> StockMovement:
        model = StockMovementModel(
            id=movement.id,
            tenant_id=movement.tenant_id,
            inventory_item_id=movement.inventory_item_id,
            movement_type=movement.movement_type,
            quantity_delta=movement.quantity_delta,
            reason=movement.reason,
            order_id=movement.order_id,
        )
        created = await super().add_model(model)
        return _to_entity(created)

    async def list_by_item(self, inventory_item_id: uuid.UUID) -> list[StockMovement]:
        stmt = (
            select(self.model)
            .where(
                self.model.inventory_item_id == inventory_item_id,
                self.model.tenant_id == self._tenant_id,
                self.model.deleted_at.is_(None),
            )
            .order_by(self.model.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return [_to_entity(m) for m in result.scalars().all()]
