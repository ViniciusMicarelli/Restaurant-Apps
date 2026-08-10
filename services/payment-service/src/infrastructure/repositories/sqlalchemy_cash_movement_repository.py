"""Implementação concreta de `CashMovementRepositoryInterface` sobre SQLAlchemy 2.0 Async.

`CashMovement` é append-only (auditoria) — este repositório nunca atualiza
ou remove um registro já criado.
"""

from __future__ import annotations

import uuid

from restaurant_database import SQLAlchemyRepository
from sqlalchemy import select
from src.domain.entities.cash_movement import CashMovement
from src.infrastructure.models.cash_movement_model import CashMovementModel


def _to_entity(model: CashMovementModel) -> CashMovement:
    return CashMovement(
        id=model.id,
        tenant_id=model.tenant_id,
        cash_register_id=model.cash_register_id,
        movement_type=model.movement_type,
        amount_delta=model.amount_delta,
        reason=model.reason,
        payment_id=model.payment_id,
        created_at=model.created_at,
    )


class SQLAlchemyCashMovementRepository(SQLAlchemyRepository[CashMovementModel]):
    model = CashMovementModel

    async def add(self, movement: CashMovement) -> CashMovement:
        model = CashMovementModel(
            id=movement.id,
            tenant_id=movement.tenant_id,
            cash_register_id=movement.cash_register_id,
            movement_type=movement.movement_type,
            amount_delta=movement.amount_delta,
            reason=movement.reason,
            payment_id=movement.payment_id,
        )
        created = await super().add_model(model)
        return _to_entity(created)

    async def list_by_register(self, cash_register_id: uuid.UUID) -> list[CashMovement]:
        stmt = (
            select(self.model)
            .where(
                self.model.cash_register_id == cash_register_id,
                self.model.tenant_id == self._tenant_id,
                self.model.deleted_at.is_(None),
            )
            .order_by(self.model.created_at.asc())
        )
        result = await self._session.execute(stmt)
        return [_to_entity(m) for m in result.scalars().all()]
