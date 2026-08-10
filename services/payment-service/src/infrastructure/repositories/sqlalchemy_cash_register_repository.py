"""Implementação concreta de `CashRegisterRepositoryInterface` sobre SQLAlchemy 2.0 Async."""

from __future__ import annotations

import uuid

from restaurant_database import SQLAlchemyRepository
from sqlalchemy import select
from src.domain.entities.cash_register import CashRegister, CashRegisterStatus
from src.infrastructure.models.cash_register_model import CashRegisterModel


def _to_entity(model: CashRegisterModel) -> CashRegister:
    return CashRegister(
        id=model.id,
        tenant_id=model.tenant_id,
        operator_id=model.operator_id,
        opening_amount=model.opening_amount,
        current_balance=model.current_balance,
        status=model.status,
        opened_at=model.opened_at,
        closed_at=model.closed_at,
        closing_counted_amount=model.closing_counted_amount,
        closing_divergence=model.closing_divergence,
    )


class SQLAlchemyCashRegisterRepository(SQLAlchemyRepository[CashRegisterModel]):
    model = CashRegisterModel

    async def get_by_id(self, cash_register_id: uuid.UUID) -> CashRegister | None:
        model = await super().get_model_by_id(cash_register_id)
        return _to_entity(model) if model is not None else None

    async def get_open_by_operator(self, operator_id: uuid.UUID) -> CashRegister | None:
        stmt = select(self.model).where(
            self.model.operator_id == operator_id,
            self.model.tenant_id == self._tenant_id,
            self.model.status == CashRegisterStatus.OPEN,
            self.model.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def add(self, cash_register: CashRegister) -> CashRegister:
        if cash_register.opened_at is None:
            msg = "CashRegister.opened_at deveria estar sempre preenchido após __post_init__."
            raise RuntimeError(msg)
        model = CashRegisterModel(
            id=cash_register.id,
            tenant_id=cash_register.tenant_id,
            operator_id=cash_register.operator_id,
            opening_amount=cash_register.opening_amount,
            current_balance=cash_register.current_balance,
            status=cash_register.status,
            opened_at=cash_register.opened_at,
            closed_at=cash_register.closed_at,
            closing_counted_amount=cash_register.closing_counted_amount,
            closing_divergence=cash_register.closing_divergence,
        )
        created = await super().add_model(model)
        return _to_entity(created)

    async def save(self, cash_register: CashRegister) -> CashRegister:
        model = await self._session.get(CashRegisterModel, cash_register.id)
        if model is None:
            msg = f"Caixa '{cash_register.id}' não encontrado para atualização."
            raise LookupError(msg)
        model.current_balance = cash_register.current_balance
        model.status = cash_register.status
        model.closed_at = cash_register.closed_at
        model.closing_counted_amount = cash_register.closing_counted_amount
        model.closing_divergence = cash_register.closing_divergence
        saved = await super().save_model(model)
        return _to_entity(saved)
