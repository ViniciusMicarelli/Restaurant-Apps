"""Caso de uso: criação de uma entrega a partir de um pedido de delivery."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from restaurant_core.ids import generate_uuid7
from src.application.dtos.delivery_dtos import DeliveryResponse
from src.application.interfaces.repository_interface import DeliveryRepositoryInterface
from src.application.use_cases._shared import to_delivery_response
from src.domain.entities.delivery import Delivery


@dataclass
class CreateDeliveryUseCase:
    delivery_repository: DeliveryRepositoryInterface

    async def execute(
        self, *, tenant_id: uuid.UUID, order_id: uuid.UUID, delivery_address: str
    ) -> DeliveryResponse:
        delivery = Delivery(
            id=generate_uuid7(),
            tenant_id=tenant_id,
            order_id=order_id,
            delivery_address=delivery_address,
        )
        created = await self.delivery_repository.add(delivery)
        return to_delivery_response(created)


@dataclass
class ListDeliveriesUseCase:
    delivery_repository: DeliveryRepositoryInterface

    async def execute(self) -> list[DeliveryResponse]:
        deliveries = await self.delivery_repository.list_all()
        return [to_delivery_response(d) for d in deliveries]
