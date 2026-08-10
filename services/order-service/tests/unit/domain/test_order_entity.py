"""Testes da entidade de domínio `Order` (cálculo de total + máquina de estados)."""

import uuid
from typing import Any

import pytest
from src.domain.entities.order import Order, OrderItem, OrderStatus, OrderType


def _make_order(**overrides: Any) -> Order:
    defaults: dict[str, Any] = {
        "id": uuid.uuid4(),
        "tenant_id": uuid.uuid4(),
        "order_type": OrderType.TABLE,
        "table_number": 5,
        "items": [
            OrderItem(product_id=uuid.uuid4(), product_name="X-Burger", unit_price=30.0, quantity=2)
        ],
    }
    defaults.update(overrides)
    return Order(**defaults)


def test_order_total_calculation() -> None:
    items = [
        OrderItem(
            product_id=uuid.uuid4(), product_name="Hambúrguer", unit_price=30.00, quantity=2
        ),  # 60.00
        OrderItem(
            product_id=uuid.uuid4(), product_name="Coca-Cola", unit_price=7.50, quantity=3
        ),  # 22.50
    ]
    order = _make_order(items=items)

    assert order.total_amount == 82.50


def test_order_item_rejects_negative_price() -> None:
    with pytest.raises(ValueError, match="preço unitário"):
        OrderItem(product_id=uuid.uuid4(), product_name="X", unit_price=-1.0)


def test_order_item_rejects_zero_quantity() -> None:
    with pytest.raises(ValueError, match="quantidade"):
        OrderItem(product_id=uuid.uuid4(), product_name="X", unit_price=10.0, quantity=0)


def test_order_requires_at_least_one_item() -> None:
    with pytest.raises(ValueError, match="ao menos um item"):
        _make_order(items=[])


def test_new_order_starts_pending() -> None:
    order = _make_order()
    assert order.status.value == "PENDING"


def test_pending_order_transitions_to_preparing() -> None:
    order = _make_order()
    order.transition_to(OrderStatus.PREPARING)
    assert order.status.value == "PREPARING"


def test_preparing_order_transitions_to_ready() -> None:
    order = _make_order()
    order.transition_to(OrderStatus.PREPARING)
    order.transition_to(OrderStatus.READY)
    assert order.status.value == "READY"


def test_ready_order_transitions_to_delivered() -> None:
    order = _make_order()
    order.transition_to(OrderStatus.PREPARING)
    order.transition_to(OrderStatus.READY)
    order.transition_to(OrderStatus.DELIVERED)
    assert order.status.value == "DELIVERED"


def test_order_state_machine_invalid_transition_raises_error() -> None:
    order = _make_order()

    with pytest.raises(ValueError, match="Transição inválida de estado"):
        order.transition_to(OrderStatus.DELIVERED)


def test_cancel_sets_status_and_reason() -> None:
    order = _make_order()
    order.cancel("Cliente desistiu")

    assert order.status.value == "CANCELLED"
    assert order.cancellation_reason == "Cliente desistiu"


def test_cancel_requires_non_empty_reason() -> None:
    order = _make_order()
    with pytest.raises(ValueError, match="motivo"):
        order.cancel("   ")


def test_cannot_cancel_a_delivered_order() -> None:
    order = _make_order()
    order.transition_to(OrderStatus.PREPARING)
    order.transition_to(OrderStatus.READY)
    order.transition_to(OrderStatus.DELIVERED)

    with pytest.raises(ValueError, match="Transição inválida de estado"):
        order.cancel("Mudou de ideia")
