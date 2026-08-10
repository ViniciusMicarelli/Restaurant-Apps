"""Fakes em memória dos contratos do `kitchen-service` — usados pelos testes unitários."""

from __future__ import annotations

import uuid
from typing import Any

from src.domain.entities.kds_item import KDSItem, KDSStation
from src.domain.entities.kds_log import KDSLog


class FakeKDSItemStore:
    def __init__(self, items: list[KDSItem] | None = None) -> None:
        self._items: dict[uuid.UUID, KDSItem] = {i.id: i for i in (items or [])}

    async def get_by_id(self, kds_item_id: uuid.UUID) -> KDSItem | None:
        return self._items.get(kds_item_id)

    async def list_all(self, *, station: KDSStation | None = None) -> list[KDSItem]:
        items = list(self._items.values())
        if station is not None:
            items = [i for i in items if i.station == station]
        return items

    async def add(self, item: KDSItem) -> KDSItem:
        self._items[item.id] = item
        return item

    async def save(self, item: KDSItem) -> KDSItem:
        self._items[item.id] = item
        return item


class FakeKDSLogStore:
    def __init__(self) -> None:
        self.logs: list[KDSLog] = []

    async def add(self, log: KDSLog) -> KDSLog:
        self.logs.append(log)
        return log


class FakeBroadcaster:
    def __init__(self) -> None:
        self.messages: list[tuple[uuid.UUID, dict[str, Any]]] = []

    async def broadcast(self, tenant_id: uuid.UUID, message: dict[str, Any]) -> None:
        self.messages.append((tenant_id, message))
