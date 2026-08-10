"""Casos de uso: atribuição de entregador e transição de status de uma entrega."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from restaurant_core.exceptions import ResourceNotFoundException
from src.application.dtos.delivery_dtos import DeliveryResponse
from src.application.interfaces.repository_interface import DeliveryRepositoryInterface
from src.application.use_cases._shared import to_delivery_response
from src.domain.entities.delivery import DeliveryStatus
from src.domain.exceptions import InvalidDeliveryTransitionError


@dataclass
class AssignCourierUseCase:
    delivery_repository: DeliveryRepositoryInterface

    async def execute(self, *, delivery_id: uuid.UUID, courier_name: str) -> DeliveryResponse:
        delivery = await self.delivery_repository.get_by_id(delivery_id)
        if delivery is None:
            raise ResourceNotFoundException("Delivery", str(delivery_id))

        try:
            delivery.assign_courier(courier_name)
        except ValueError as exc:
            raise InvalidDeliveryTransitionError(str(exc)) from exc

        saved = await self.delivery_repository.save(delivery)
        return to_delivery_response(saved)


@dataclass
class UpdateDeliveryStatusUseCase:
    delivery_repository: DeliveryRepositoryInterface

    async def execute(
        self, *, delivery_id: uuid.UUID, new_status: DeliveryStatus
    ) -> DeliveryResponse:
        delivery = await self.delivery_repository.get_by_id(delivery_id)
        if delivery is None:
            raise ResourceNotFoundException("Delivery", str(delivery_id))

        try:
            delivery.transition_to(new_status)
        except ValueError as exc:
            raise InvalidDeliveryTransitionError(str(exc)) from exc

        saved = await self.delivery_repository.save(delivery)
        return to_delivery_response(saved)
