"""Implementação concreta de `PaymentRepositoryInterface` sobre SQLAlchemy 2.0 Async."""

from __future__ import annotations

import uuid

from restaurant_database import SQLAlchemyRepository
from sqlalchemy import select
from src.domain.entities.payment import Payment, PaymentSplit, PaymentStatus
from src.infrastructure.models.payment_model import PaymentModel


def _to_entity(model: PaymentModel) -> Payment:
    return Payment(
        id=model.id,
        tenant_id=model.tenant_id,
        order_id=model.order_id,
        cash_register_id=model.cash_register_id,
        command_id=model.command_id,
        splits=[
            PaymentSplit(payment_method=s["payment_method"], amount=s["amount"])
            for s in model.splits
        ],
        status=model.status,
        idempotency_key=model.idempotency_key,
        card_last4=model.card_last4,
        card_holder_name=model.card_holder_name,
        signature_data=model.signature_data,
        created_at=model.created_at,
    )


def _splits_to_json(payment: Payment) -> list[dict[str, object]]:
    return [{"payment_method": s.payment_method.value, "amount": s.amount} for s in payment.splits]


class SQLAlchemyPaymentRepository(SQLAlchemyRepository[PaymentModel]):
    model = PaymentModel

    async def get_by_id(self, payment_id: uuid.UUID) -> Payment | None:
        model = await super().get_model_by_id(payment_id)
        return _to_entity(model) if model is not None else None

    async def list_all(
        self, *, status: PaymentStatus | None = None, command_id: uuid.UUID | None = None
    ) -> list[Payment]:
        stmt = (
            select(self.model)
            .where(self.model.tenant_id == self._tenant_id, self.model.deleted_at.is_(None))
            .order_by(self.model.created_at.desc())
            .limit(1000)
        )
        if status is not None:
            stmt = stmt.where(self.model.status == status)
        if command_id is not None:
            stmt = stmt.where(self.model.command_id == command_id)
        result = await self._session.execute(stmt)
        return [_to_entity(m) for m in result.scalars().all()]

    async def add(self, payment: Payment) -> Payment:
        model = PaymentModel(
            id=payment.id,
            tenant_id=payment.tenant_id,
            order_id=payment.order_id,
            cash_register_id=payment.cash_register_id,
            command_id=payment.command_id,
            splits=_splits_to_json(payment),
            status=payment.status,
            idempotency_key=payment.idempotency_key,
            card_last4=payment.card_last4,
            card_holder_name=payment.card_holder_name,
            signature_data=payment.signature_data,
        )
        created = await super().add_model(model)
        return _to_entity(created)
