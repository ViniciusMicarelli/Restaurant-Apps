"""Testes do envelope `DomainEvent`."""

import uuid

from restaurant_events.envelope import DomainEvent


def test_domain_event_generates_uuid7_event_id_by_default() -> None:
    event = DomainEvent(
        event_type="order.created", tenant_id=uuid.uuid4(), payload={"order_id": "abc"}
    )

    assert event.event_id.version == 7


def test_domain_event_defaults_occurred_at_to_now_and_empty_payload() -> None:
    event = DomainEvent(event_type="order.created", tenant_id=uuid.uuid4())

    assert event.payload == {}
    assert event.occurred_at is not None


def test_domain_event_round_trips_through_json_serialization() -> None:
    tenant_id = uuid.uuid4()
    event = DomainEvent(
        event_type="order.created", tenant_id=tenant_id, payload={"order_id": "abc", "total": 42.5}
    )

    restored = DomainEvent.model_validate_json(event.model_dump_json())

    assert restored.event_id == event.event_id
    assert restored.tenant_id == tenant_id
    assert restored.payload == {"order_id": "abc", "total": 42.5}
