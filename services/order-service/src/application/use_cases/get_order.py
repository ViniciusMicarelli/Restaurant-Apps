"""Casos de uso: consulta de pedido(s)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from restaurant_core.exceptions import ResourceNotFoundException
from src.application.dtos.order_dtos import OrderResponse
from src.application.interfaces.repository_interface import OrderRepositoryInterface
from src.application.use_cases._shared import to_order_response


@dataclass
class GetOrderUseCase:
    order_repository: OrderRepositoryInterface

    async def execute(self, *, order_id: uuid.UUID) -> OrderResponse:
        order = await self.order_repository.get_by_id(order_id)
        if order is None:
            raise ResourceNotFoundException("Order", str(order_id))
        return to_order_response(order)


@dataclass
class ListOrdersUseCase:
    order_repository: OrderRepositoryInterface

    async def execute(
        self, *, table_number: int | None = None, command_id: uuid.UUID | None = None
    ) -> list[OrderResponse]:
        orders = await self.order_repository.list_all(
            table_number=table_number, command_id=command_id
        )
        return [to_order_response(o) for o in orders]
