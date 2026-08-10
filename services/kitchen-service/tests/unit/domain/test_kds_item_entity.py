"""Testes da entidade de domínio `KDSItem` (máquina de estados)."""

import uuid
from typing import Any

import pytest
from src.domain.entities.kds_item import KDSItem, KDSItemStatus, KDSStation


def _make_item(**overrides: Any) -> KDSItem:
    defaults: dict[str, Any] = {
        "id": uuid.uuid4(),
        "tenant_id": uuid.uuid4(),
        "order_id": uuid.uuid4(),
        "product_id": uuid.uuid4(),
        "product_name": "X-Burger",
        "quantity": 2,
    }
    defaults.update(overrides)
    return KDSItem(**defaults)


def test_new_item_starts_pending() -> None:
    item = _make_item()
    assert item.status == KDSItemStatus.PENDING


def test_item_rejects_zero_quantity() -> None:
    with pytest.raises(ValueError, match="quantidade"):
        _make_item(quantity=0)


def test_default_station_is_cozinha_quente() -> None:
    item = _make_item()
    assert item.station == KDSStation.COZINHA_QUENTE


def test_pending_item_transitions_to_preparing() -> None:
    item = _make_item()
    item.transition_to(KDSItemStatus.PREPARING)
    assert item.status == KDSItemStatus.PREPARING


def test_preparing_item_transitions_to_ready() -> None:
    item = _make_item()
    item.transition_to(KDSItemStatus.PREPARING)
    item.transition_to(KDSItemStatus.READY)
    assert item.status == KDSItemStatus.READY


def test_ready_item_transitions_to_delivered() -> None:
    item = _make_item()
    item.transition_to(KDSItemStatus.PREPARING)
    item.transition_to(KDSItemStatus.READY)
    item.transition_to(KDSItemStatus.DELIVERED)
    assert item.status == KDSItemStatus.DELIVERED


def test_cannot_skip_states() -> None:
    item = _make_item()
    with pytest.raises(ValueError, match="Transição inválida de estado"):
        item.transition_to(KDSItemStatus.READY)


def test_delivered_item_has_no_valid_transitions() -> None:
    item = _make_item()
    item.transition_to(KDSItemStatus.PREPARING)
    item.transition_to(KDSItemStatus.READY)
    item.transition_to(KDSItemStatus.DELIVERED)

    with pytest.raises(ValueError, match="Transição inválida de estado"):
        item.transition_to(KDSItemStatus.PREPARING)


def test_transition_to_ready_stamps_ready_at() -> None:
    """Base do SLA de cozinha no dashboard do dono: created_at -> ready_at."""
    item = _make_item()
    assert item.ready_at is None

    item.transition_to(KDSItemStatus.PREPARING)
    assert item.ready_at is None  # ainda não chegou em READY

    item.transition_to(KDSItemStatus.READY)
    assert item.ready_at is not None


def test_transition_to_delivered_stamps_delivered_at() -> None:
    item = _make_item()
    item.transition_to(KDSItemStatus.PREPARING)
    item.transition_to(KDSItemStatus.READY)
    assert item.delivered_at is None

    item.transition_to(KDSItemStatus.DELIVERED)
    assert item.delivered_at is not None
