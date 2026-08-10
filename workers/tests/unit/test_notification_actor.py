"""Testes do actor Dramatiq `send_notification` — chamado diretamente (sem broker real).

Actors Dramatiq são chamáveis diretamente (`actor(...)`), o que executa a
função de fato de forma síncrona, sem passar pelo broker — ideal para testes
unitários que não precisam de um Redis real (`.send()` é o que enfileira).
"""

from __future__ import annotations

import logging

import pytest
from src.async_tasks.notification_actor import send_notification


def test_send_notification_logs_structured_message(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO):
        send_notification(
            notification_id="019fcfe2-89a9-72de-a370-c2b06c4c8072",
            channel="WHATSAPP",
            recipient="+5511999999999",
            template_code="QUEUE_POSITION",
            rendered_preview="Olá Ana, sua posição é 2.",
        )

    assert len(caplog.records) == 1
    record = caplog.records[0].getMessage()
    assert "NOTIFICATION_SENT" in record
    assert "+5511999999999" in record
    assert "QUEUE_POSITION" in record
