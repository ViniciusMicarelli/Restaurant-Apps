"""Caso de uso: cancelamento de pedido (exige motivo — registrado para auditoria)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from restaurant_core.exceptions import ResourceNotFoundException
from src.application.dtos.order_dtos import OrderResponse
from src.application.interfaces.repository_interface import OrderRepositoryInterface
from src.application.use_cases._shared import to_order_response
from src.domain.exceptions import InvalidOrderTransitionError


@dataclass
class CancelOrderUseCase:
    order_repository: OrderRepositoryInterface

    async def execute(self, *, order_id: uuid.UUID, cancellation_reason: str) -> OrderResponse:
        order = await self.order_repository.get_by_id(order_id)
        if order is None:
            raise ResourceNotFoundException("Order", str(order_id))

        try:
            order.cancel(cancellation_reason)
        except ValueError as exc:
            raise InvalidOrderTransitionError(str(exc)) from exc

        updated = await self.order_repository.save(order)
        return to_order_response(updated)
