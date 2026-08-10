"""Testes da entidade de domínio `AuditLog`."""

import uuid

import pytest
from src.domain.entities.audit_log import AuditLog


def test_rejects_empty_event_type() -> None:
    with pytest.raises(ValueError, match="tipo do evento"):
        AuditLog(id=uuid.uuid4(), tenant_id=uuid.uuid4(), event_id=uuid.uuid4(), event_type="   ")


def test_default_payload_is_empty_dict() -> None:
    log = AuditLog(
        id=uuid.uuid4(), tenant_id=uuid.uuid4(), event_id=uuid.uuid4(), event_type="order.created"
    )
    assert log.payload == {}
