"""Testes unitários de `TransitionOrderStatusUseCase` e `CancelOrderUseCase`."""

import uuid

import pytest
from restaurant_core.exceptions import ResourceNotFoundException
from restaurant_events import InMemoryEventBus
from src.application.use_cases.cancel_order import CancelOrderUseCase
from src.application.use_cases.transition_order_status import TransitionOrderStatusUseCase
from src.domain.entities.order import Order, OrderItem, OrderStatus, OrderType
from src.domain.exceptions import InvalidOrderTransitionError
from tests.unit.fakes import FakeOrderStore


def _make_order() -> Order:
    return Order(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        order_type=OrderType.TABLE,
        items=[OrderItem(product_id=uuid.uuid4(), product_name="X-Burger", unit_price=25.0)],
    )


@pytest.mark.asyncio
async def test_transition_order_status_applies_valid_transition() -> None:
    order = _make_order()
    store = FakeOrderStore([order])
    use_case = TransitionOrderStatusUseCase(order_repository=store, event_bus=InMemoryEventBus())

    response = await use_case.execute(order_id=order.id, new_status=OrderStatus.PREPARING)

    assert response.status == OrderStatus.PREPARING


@pytest.mark.asyncio
async def test_transition_order_status_publishes_status_changed_event() -> None:
    order = _make_order()
    store = FakeOrderStore([order])
    event_bus = InMemoryEventBus()
    use_case = TransitionOrderStatusUseCase(order_repository=store, event_bus=event_bus)

    await use_case.execute(order_id=order.id, new_status=OrderStatus.PREPARING)

    assert len(event_bus.published) == 1
    routing_key, event = event_bus.published[0]
    assert routing_key == "order.status_changed"
    assert event.payload["order_id"] == str(order.id)
    assert event.payload["new_status"] == "PREPARING"


@pytest.mark.asyncio
async def test_transition_order_status_rejects_invalid_transition() -> None:
    order = _make_order()
    store = FakeOrderStore([order])
    use_case = TransitionOrderStatusUseCase(order_repository=store, event_bus=InMemoryEventBus())

    with pytest.raises(InvalidOrderTransitionError):
        await use_case.execute(order_id=order.id, new_status=OrderStatus.DELIVERED)


@pytest.mark.asyncio
async def test_transition_order_status_raises_not_found_for_unknown_order() -> None:
    use_case = TransitionOrderStatusUseCase(
        order_repository=FakeOrderStore(), event_bus=InMemoryEventBus()
    )

    with pytest.raises(ResourceNotFoundException):
        await use_case.execute(order_id=uuid.uuid4(), new_status=OrderStatus.PREPARING)


@pytest.mark.asyncio
async def test_cancel_order_sets_reason_and_status() -> None:
    order = _make_order()
    store = FakeOrderStore([order])
    use_case = CancelOrderUseCase(order_repository=store)

    response = await use_case.execute(order_id=order.id, cancellation_reason="Cliente desistiu")

    assert response.status == OrderStatus.CANCELLED
    assert response.cancellation_reason == "Cliente desistiu"


@pytest.mark.asyncio
async def test_cancel_order_raises_not_found_for_unknown_order() -> None:
    use_case = CancelOrderUseCase(order_repository=FakeOrderStore())

    with pytest.raises(ResourceNotFoundException):
        await use_case.execute(order_id=uuid.uuid4(), cancellation_reason="Motivo qualquer")
