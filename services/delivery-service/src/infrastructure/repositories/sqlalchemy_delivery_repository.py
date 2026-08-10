"""Implementação concreta de `DeliveryRepositoryInterface` sobre SQLAlchemy 2.0 Async."""

from __future__ import annotations

import uuid

from restaurant_database import SQLAlchemyRepository
from src.domain.entities.delivery import Delivery
from src.infrastructure.models.delivery_model import DeliveryModel


def _to_entity(model: DeliveryModel) -> Delivery:
    return Delivery(
        id=model.id,
        tenant_id=model.tenant_id,
        order_id=model.order_id,
        delivery_address=model.delivery_address,
        courier_name=model.courier_name,
        status=model.status,
    )


class SQLAlchemyDeliveryRepository(SQLAlchemyRepository[DeliveryModel]):
    model = DeliveryModel

    async def get_by_id(self, delivery_id: uuid.UUID) -> Delivery | None:
        model = await super().get_model_by_id(delivery_id)
        return _to_entity(model) if model is not None else None

    async def list_all(self) -> list[Delivery]:
        models = await super().list_models(limit=1000)
        return [_to_entity(m) for m in models]

    async def add(self, delivery: Delivery) -> Delivery:
        model = DeliveryModel(
            id=delivery.id,
            tenant_id=delivery.tenant_id,
            order_id=delivery.order_id,
            delivery_address=delivery.delivery_address,
            courier_name=delivery.courier_name,
            status=delivery.status,
        )
        created = await super().add_model(model)
        return _to_entity(created)

    async def save(self, delivery: Delivery) -> Delivery:
        model = await self._session.get(DeliveryModel, delivery.id)
        if model is None:
            msg = f"Entrega '{delivery.id}' não encontrada para atualização."
            raise LookupError(msg)
        model.courier_name = delivery.courier_name
        model.status = delivery.status
        saved = await super().save_model(model)
        return _to_entity(saved)
