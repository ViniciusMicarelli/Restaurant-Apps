"""Fake em memória de `OrderRepositoryInterface` — usado pelos testes unitários.

Para `IdempotencyStoreInterface` e `EventBus`, os testes reaproveitam as
implementações em memória já existentes (`InMemoryIdempotencyStore` do
próprio serviço e `InMemoryEventBus` de `restaurant_events`) — não há
necessidade de duplicar fakes que já existem e já são testados.
"""

from __future__ import annotations

import uuid

from src.domain.entities.order import Order


class FakeOrderStore:
    def __init__(self, orders: list[Order] | None = None) -> None:
        self._orders: dict[uuid.UUID, Order] = {o.id: o for o in (orders or [])}

    async def get_by_id(self, order_id: uuid.UUID) -> Order | None:
        return self._orders.get(order_id)

    async def list_all(
        self, *, table_number: int | None = None, command_id: uuid.UUID | None = None
    ) -> list[Order]:
        orders = list(self._orders.values())
        if table_number is not None:
            orders = [o for o in orders if o.table_number == table_number]
        if command_id is not None:
            orders = [o for o in orders if o.command_id == command_id]
        return orders

    async def add(self, order: Order) -> Order:
        self._orders[order.id] = order
        return order

    async def save(self, order: Order) -> Order:
        self._orders[order.id] = order
        return order
