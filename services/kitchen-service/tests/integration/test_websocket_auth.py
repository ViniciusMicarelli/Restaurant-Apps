"""Testes de autenticação do WebSocket do KDS (`/ws/v1/kitchen/kds`)."""

from __future__ import annotations

import uuid

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from restaurant_security.jwt import create_access_token
from starlette.websockets import WebSocketDisconnect

SECRET = "integration-test-secret-key-32chars"


def test_websocket_rejects_missing_token(client: TestClient) -> None:
    with pytest.raises(WebSocketDisconnect), client.websocket_connect("/ws/v1/kitchen/kds"):
        pass


def test_websocket_rejects_role_without_kitchen_access(client: TestClient) -> None:
    token = create_access_token(str(uuid.uuid4()), str(uuid.uuid4()), "CUSTOMER", SECRET)
    with (
        pytest.raises(WebSocketDisconnect) as exc_info,
        client.websocket_connect(f"/ws/v1/kitchen/kds?token={token}"),
    ):
        pass

    assert exc_info.value.code == status.WS_1008_POLICY_VIOLATION


def test_websocket_accepts_kitchen_staff_and_responds_to_ping(client: TestClient) -> None:
    token = create_access_token(str(uuid.uuid4()), str(uuid.uuid4()), "KITCHEN_STAFF", SECRET)
    with client.websocket_connect(f"/ws/v1/kitchen/kds?token={token}") as websocket:
        websocket.send_text("ping")
        response = websocket.receive_json()
        assert response == {"event": "PONG", "payload": "ping"}
