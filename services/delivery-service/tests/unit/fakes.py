"""Fake em memória de `DeliveryRepositoryInterface` — usado pelos testes unitários."""

from __future__ import annotations

import uuid

from src.domain.entities.delivery import Delivery


class FakeDeliveryStore:
    def __init__(self, deliveries: list[Delivery] | None = None) -> None:
        self._deliveries: dict[uuid.UUID, Delivery] = {d.id: d for d in (deliveries or [])}

    async def get_by_id(self, delivery_id: uuid.UUID) -> Delivery | None:
        return self._deliveries.get(delivery_id)

    async def list_all(self) -> list[Delivery]:
        return list(self._deliveries.values())

    async def add(self, delivery: Delivery) -> Delivery:
        self._deliveries[delivery.id] = delivery
        return delivery

    async def save(self, delivery: Delivery) -> Delivery:
        self._deliveries[delivery.id] = delivery
        return delivery
