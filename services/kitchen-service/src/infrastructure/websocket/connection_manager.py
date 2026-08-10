"""Gerenciador de conexões WebSocket ativas nos monitores de cozinha (KDS).

Escopado por `tenant_id`: cada broadcast só alcança as telas conectadas do
mesmo restaurante, nunca vazando pedidos entre tenants (ADR-003).
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any, Protocol


class _WebSocketLike(Protocol):
    """Superfície mínima de `fastapi.WebSocket` usada por este gerenciador.

    Um `Protocol` estrutural (em vez do tipo concreto `fastapi.WebSocket`)
    permite que os testes usem um dublê simples sem depender de um servidor
    ASGI real, mantendo a checagem de tipos estrita.
    """

    async def accept(self) -> None: ...

    async def send_text(self, data: str) -> None: ...


logger = logging.getLogger(__name__)


class KDSConnectionManager:
    """Implementa `KDSBroadcasterInterface` sobre WebSockets do FastAPI."""

    def __init__(self) -> None:
        self._connections: dict[uuid.UUID, list[_WebSocketLike]] = {}

    async def connect(self, websocket: _WebSocketLike, tenant_id: uuid.UUID) -> None:
        await websocket.accept()
        self._connections.setdefault(tenant_id, []).append(websocket)

    def disconnect(self, websocket: _WebSocketLike, tenant_id: uuid.UUID) -> None:
        connections = self._connections.get(tenant_id)
        if connections and websocket in connections:
            connections.remove(websocket)

    async def broadcast(self, tenant_id: uuid.UUID, message: dict[str, Any]) -> None:
        connections = self._connections.get(tenant_id, [])
        payload = json.dumps(message)
        for connection in connections:
            try:
                await connection.send_text(payload)
            except Exception:  # deliberado: uma conexão morta não deve derrubar o broadcast
                logger.warning(
                    "Falha ao enviar mensagem para conexão WebSocket do KDS.", exc_info=True
                )
