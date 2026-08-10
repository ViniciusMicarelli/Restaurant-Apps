"""Testes do handler de bridge `notification.requested` → Dramatiq.

`enqueue` é injetado explicitamente (não usa `send_notification.send` real),
então nenhuma conexão Redis é necessária.
"""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import MagicMock

import pytest
from restaurant_events import DomainEvent
from src.consumers.notification_bridge import build_notification_requested_handler


@pytest.mark.asyncio
async def test_handler_enqueues_the_actor_with_payload_fields() -> None:
    enqueue = MagicMock()
    handler = build_notification_requested_handler(enqueue=enqueue)
    payload: dict[str, Any] = {
        "notification_id": str(uuid.uuid4()),
        "channel": "WHATSAPP",
        "recipient": "+5511999999999",
        "template_code": "QUEUE_POSITION",
        "rendered_preview": "Olá Ana, sua posição é 2.",
    }
    event = DomainEvent(
        event_type="notification.requested", tenant_id=uuid.uuid4(), payload=payload
    )

    await handler(event)

    enqueue.assert_called_once_with(
        notification_id=payload["notification_id"],
        channel="WHATSAPP",
        recipient="+5511999999999",
        template_code="QUEUE_POSITION",
        rendered_preview="Olá Ana, sua posição é 2.",
    )
