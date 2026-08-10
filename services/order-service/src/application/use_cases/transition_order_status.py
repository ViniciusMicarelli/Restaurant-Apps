"""Caso de uso: transição de status de um pedido (PENDING → PREPARING → READY → DELIVERED).

Publica `order.status_changed` (`restaurant_events`) a cada transição —
consumido pelo `notification-service` para avisar (in-app, por ora) quando um
pedido fica pronto (docs/modules/module_breakdown.md §11).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from restaurant_core.exceptions import ResourceNotFoundException
from restaurant_events import DomainEvent, EventBus
from src.application.dtos.order_dtos import OrderResponse
from src.application.interfaces.repository_interface import OrderRepositoryInterface
from src.application.use_cases._shared import to_order_response
from src.domain.entities.order import OrderStatus
from src.domain.exceptions import InvalidOrderTransitionError

ORDER_STATUS_CHANGED_ROUTING_KEY = "order.status_changed"


@dataclass
class TransitionOrderStatusUseCase:
    order_repository: OrderRepositoryInterface
    event_bus: EventBus

    async def execute(self, *, order_id: uuid.UUID, new_status: OrderStatus) -> OrderResponse:
        order = await self.order_repository.get_by_id(order_id)
        if order is None:
            raise ResourceNotFoundException("Order", str(order_id))

        try:
            order.transition_to(new_status)
        except ValueError as exc:
            raise InvalidOrderTransitionError(str(exc)) from exc

        updated = await self.order_repository.save(order)

        await self.event_bus.publish(
            DomainEvent(
                event_type=ORDER_STATUS_CHANGED_ROUTING_KEY,
                tenant_id=updated.tenant_id,
                payload={
                    "order_id": str(updated.id),
                    "table_number": updated.table_number,
                    "new_status": updated.status.value,
                },
            ),
            routing_key=ORDER_STATUS_CHANGED_ROUTING_KEY,
        )

        return to_order_response(updated)
