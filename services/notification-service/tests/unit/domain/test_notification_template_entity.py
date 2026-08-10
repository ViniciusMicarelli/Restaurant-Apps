"""Testes da entidade de domínio `NotificationTemplate`."""

import uuid
from typing import Any

import pytest
from src.domain.entities.notification_template import NotificationChannel, NotificationTemplate


def _make_template(**overrides: Any) -> NotificationTemplate:
    defaults: dict[str, Any] = {
        "id": uuid.uuid4(),
        "tenant_id": uuid.uuid4(),
        "code": "queue_position",
        "channel": NotificationChannel.WHATSAPP,
        "body": "Olá {nome}, sua posição na fila é {posicao}.",
    }
    defaults.update(overrides)
    return NotificationTemplate(**defaults)


def test_code_is_normalized_to_uppercase() -> None:
    template = _make_template(code="queue_position")
    assert template.code == "QUEUE_POSITION"


def test_rejects_empty_body() -> None:
    with pytest.raises(ValueError, match="corpo"):
        _make_template(body="   ")


def test_email_requires_subject() -> None:
    with pytest.raises(ValueError, match="assunto"):
        _make_template(channel=NotificationChannel.EMAIL, subject=None)


def test_email_with_subject_is_valid() -> None:
    template = _make_template(
        channel=NotificationChannel.EMAIL, subject="Confirmação de reserva", body="Olá {nome}."
    )
    assert template.subject == "Confirmação de reserva"


def test_render_substitutes_placeholders() -> None:
    template = _make_template()
    rendered = template.render({"nome": "Ana", "posicao": "3"})
    assert rendered == "Olá Ana, sua posição na fila é 3."


def test_render_raises_on_missing_context_key() -> None:
    template = _make_template()
    with pytest.raises(ValueError, match="Contexto incompleto"):
        template.render({"nome": "Ana"})
