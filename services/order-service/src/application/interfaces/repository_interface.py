"""Contratos de repositório e infraestrutura do motor de pedidos."""

from __future__ import annotations

import uuid
from typing import Protocol

from src.domain.entities.order import Order


class OrderRepositoryInterface(Protocol):
    async def get_by_id(self, order_id: uuid.UUID) -> Order | None: ...

    async def list_all(
        self, *, table_number: int | None = None, command_id: uuid.UUID | None = None
    ) -> list[Order]: ...

    async def add(self, order: Order) -> Order: ...

    async def save(self, order: Order) -> Order: ...


class IdempotencyStoreInterface(Protocol):
    """Armazenamento de chaves de idempotência (Redis DB 4 — docs/DATABASE.md).

    Evita que reenvios de rede (timeout + retry do cliente) criem pedidos
    duplicados: a mesma `Idempotency-Key` sempre retorna o `order_id` já
    criado na primeira tentativa, em vez de processar de novo.
    """

    async def get_order_id(self, idempotency_key: str) -> uuid.UUID | None: ...

    async def set_order_id(
        self, idempotency_key: str, order_id: uuid.UUID, ttl_seconds: int = 86400
    ) -> None: ...
