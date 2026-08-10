"""Testes do `KDSConnectionManager` — garante isolamento de broadcast por tenant (ADR-003)."""

from __future__ import annotations

import uuid

import pytest
from src.infrastructure.websocket.connection_manager import KDSConnectionManager


class FakeWebSocket:
    """Substitui `fastapi.WebSocket` nos testes — sem servidor ASGI real."""

    def __init__(self) -> None:
        self.accepted = False
        self.received: list[str] = []

    async def accept(self) -> None:
        self.accepted = True

    async def send_text(self, data: str) -> None:
        self.received.append(data)


@pytest.mark.asyncio
async def test_connect_accepts_the_websocket() -> None:
    manager = KDSConnectionManager()
    ws = FakeWebSocket()

    await manager.connect(ws, uuid.uuid4())

    assert ws.accepted is True


@pytest.mark.asyncio
async def test_broadcast_reaches_only_connections_of_the_same_tenant() -> None:
    manager = KDSConnectionManager()
    tenant_a, tenant_b = uuid.uuid4(), uuid.uuid4()
    ws_a, ws_b = FakeWebSocket(), FakeWebSocket()

    await manager.connect(ws_a, tenant_a)
    await manager.connect(ws_b, tenant_b)

    await manager.broadcast(tenant_a, {"event": "KDS_ITEM_STATUS_CHANGED"})

    assert len(ws_a.received) == 1
    assert len(ws_b.received) == 0


@pytest.mark.asyncio
async def test_disconnect_removes_the_connection() -> None:
    manager = KDSConnectionManager()
    tenant_id = uuid.uuid4()
    ws = FakeWebSocket()
    await manager.connect(ws, tenant_id)

    manager.disconnect(ws, tenant_id)
    await manager.broadcast(tenant_id, {"event": "KDS_ITEM_STATUS_CHANGED"})

    assert len(ws.received) == 0
