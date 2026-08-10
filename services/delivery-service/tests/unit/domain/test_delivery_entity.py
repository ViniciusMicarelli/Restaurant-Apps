"""Testes da entidade de domínio `Delivery` (máquina de estados)."""

import uuid
from typing import Any

import pytest
from src.domain.entities.delivery import Delivery, DeliveryStatus


def _make_delivery(**overrides: Any) -> Delivery:
    defaults: dict[str, Any] = {
        "id": uuid.uuid4(),
        "tenant_id": uuid.uuid4(),
        "order_id": uuid.uuid4(),
        "delivery_address": "Rua das Flores, 123",
    }
    defaults.update(overrides)
    return Delivery(**defaults)


def test_delivery_rejects_empty_address() -> None:
    with pytest.raises(ValueError, match="endereço"):
        _make_delivery(delivery_address="   ")


def test_new_delivery_starts_pending() -> None:
    delivery = _make_delivery()
    assert delivery.status == DeliveryStatus.PENDING


def test_assign_courier_transitions_to_assigned() -> None:
    delivery = _make_delivery()
    delivery.assign_courier("João Motoboy")
    assert delivery.status == DeliveryStatus.ASSIGNED
    assert delivery.courier_name == "João Motoboy"


def test_assign_courier_rejects_empty_name() -> None:
    delivery = _make_delivery()
    with pytest.raises(ValueError, match="entregador"):
        delivery.assign_courier("   ")


def test_full_delivery_flow() -> None:
    delivery = _make_delivery()
    delivery.assign_courier("João Motoboy")
    delivery.transition_to(DeliveryStatus.IN_TRANSIT)
    delivery.transition_to(DeliveryStatus.DELIVERED)
    assert delivery.status == DeliveryStatus.DELIVERED


def test_cannot_skip_states() -> None:
    delivery = _make_delivery()
    with pytest.raises(ValueError, match="Transição inválida de estado"):
        delivery.transition_to(DeliveryStatus.DELIVERED)


def test_cancel_from_pending() -> None:
    delivery = _make_delivery()
    delivery.transition_to(DeliveryStatus.CANCELLED)
    assert delivery.status == DeliveryStatus.CANCELLED


def test_cannot_transition_a_delivered_delivery() -> None:
    delivery = _make_delivery()
    delivery.assign_courier("João Motoboy")
    delivery.transition_to(DeliveryStatus.IN_TRANSIT)
    delivery.transition_to(DeliveryStatus.DELIVERED)

    with pytest.raises(ValueError, match="Transição inválida de estado"):
        delivery.transition_to(DeliveryStatus.CANCELLED)
