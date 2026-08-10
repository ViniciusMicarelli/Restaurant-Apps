"""Contratos de repositório e infraestrutura do serviço de Cozinha/KDS."""

from __future__ import annotations

import uuid
from typing import Any, Protocol

from src.domain.entities.kds_item import KDSItem, KDSStation
from src.domain.entities.kds_log import KDSLog


class KDSItemRepositoryInterface(Protocol):
    async def get_by_id(self, kds_item_id: uuid.UUID) -> KDSItem | None: ...

    async def list_all(self, *, station: KDSStation | None = None) -> list[KDSItem]: ...

    async def add(self, item: KDSItem) -> KDSItem: ...

    async def save(self, item: KDSItem) -> KDSItem: ...


class KDSLogRepositoryInterface(Protocol):
    async def add(self, log: KDSLog) -> KDSLog: ...


class KDSBroadcasterInterface(Protocol):
    """Transmissão em tempo real para os monitores KDS conectados (WebSocket).

    Escopada por tenant — nenhuma mensagem de um restaurante pode vazar para
    a tela de outro restaurante conectado ao mesmo serviço (ADR-003).
    """

    async def broadcast(self, tenant_id: uuid.UUID, message: dict[str, Any]) -> None: ...
