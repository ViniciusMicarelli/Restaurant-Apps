"""Caso de uso: criação de um pedido, com idempotência e disparo da Saga.

Ao criar um pedido, publica o evento `order.created` (`restaurant_events`),
consumido de forma assíncrona e desacoplada por `inventory-service` (baixa
de estoque) e `kitchen-service` (criação do item no KDS) — Saga por
coreografia (ADR-001), sem acoplamento direto entre os serviços.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from restaurant_core.ids import generate_uuid7
from restaurant_events import DomainEvent, EventBus
from src.application.dtos.order_dtos import CreateOrderItemRequest, OrderResponse
from src.application.interfaces.repository_interface import (
    IdempotencyStoreInterface,
    OrderRepositoryInterface,
)
from src.application.use_cases._shared import to_order_response
from src.domain.entities.order import Order, OrderItem, OrderType

ORDER_CREATED_ROUTING_KEY = "order.created"


@dataclass
class CreateOrderUseCase:
    order_repository: OrderRepositoryInterface
    idempotency_store: IdempotencyStoreInterface
    event_bus: EventBus

    async def execute(  # noqa: PLR0913 - parâmetros nomeados (keyword-only) mapeando 1:1 com o DTO de entrada
        self,
        *,
        tenant_id: uuid.UUID,
        order_type: OrderType,
        items: list[CreateOrderItemRequest],
        table_number: int | None = None,
        command_id: uuid.UUID | None = None,
        idempotency_key: str | None = None,
    ) -> OrderResponse:
        if idempotency_key:
            existing_order_id = await self.idempotency_store.get_order_id(idempotency_key)
            if existing_order_id is not None:
                existing_order = await self.order_repository.get_by_id(existing_order_id)
                if existing_order is not None:
                    return to_order_response(existing_order)

        domain_items = [
            OrderItem(
                product_id=item.product_id,
                product_name=item.product_name,
                unit_price=item.unit_price,
                quantity=item.quantity,
                notes=item.notes,
            )
            for item in items
        ]

        order = Order(
            id=generate_uuid7(),
            tenant_id=tenant_id,
            order_type=order_type,
            table_number=table_number,
            command_id=command_id,
            items=domain_items,
        )
        created = await self.order_repository.add(order)

        if idempotency_key:
            await self.idempotency_store.set_order_id(idempotency_key, created.id)

        await self.event_bus.publish(
            DomainEvent(
                event_type=ORDER_CREATED_ROUTING_KEY,
                tenant_id=tenant_id,
                payload={
                    "order_id": str(created.id),
                    "table_number": created.table_number,
                    "items": [
                        {
                            "product_id": str(i.product_id),
                            "quantity": i.quantity,
                            "product_name": i.product_name,
                        }
                        for i in created.items
                    ],
                },
            ),
            routing_key=ORDER_CREATED_ROUTING_KEY,
        )

        return to_order_response(created)
