"""Testes unitários de `CreateOrderUseCase`: criação, Saga e idempotência."""

import uuid

import pytest
from restaurant_events import InMemoryEventBus
from src.application.dtos.order_dtos import CreateOrderItemRequest
from src.application.use_cases.create_order import ORDER_CREATED_ROUTING_KEY, CreateOrderUseCase
from src.domain.entities.order import OrderType
from src.infrastructure.cache.idempotency_store import InMemoryIdempotencyStore
from tests.unit.fakes import FakeOrderStore


def _items() -> list[CreateOrderItemRequest]:
    return [
        CreateOrderItemRequest(
            product_id=uuid.uuid4(), product_name="X-Burger", unit_price=25.0, quantity=2
        )
    ]


@pytest.mark.asyncio
async def test_create_order_persists_and_computes_total() -> None:
    use_case = CreateOrderUseCase(
        order_repository=FakeOrderStore(),
        idempotency_store=InMemoryIdempotencyStore(),
        event_bus=InMemoryEventBus(),
    )

    response = await use_case.execute(
        tenant_id=uuid.uuid4(), order_type=OrderType.TABLE, items=_items(), table_number=5
    )

    assert response.status.value == "PENDING"
    assert response.total_amount == 50.0


@pytest.mark.asyncio
async def test_create_order_publishes_order_created_event() -> None:
    event_bus = InMemoryEventBus()
    use_case = CreateOrderUseCase(
        order_repository=FakeOrderStore(),
        idempotency_store=InMemoryIdempotencyStore(),
        event_bus=event_bus,
    )

    response = await use_case.execute(
        tenant_id=uuid.uuid4(), order_type=OrderType.COUNTER, items=_items()
    )

    assert len(event_bus.published) == 1
    routing_key, event = event_bus.published[0]
    assert routing_key == ORDER_CREATED_ROUTING_KEY
    assert event.payload["order_id"] == str(response.id)


@pytest.mark.asyncio
async def test_create_order_with_same_idempotency_key_returns_the_same_order() -> None:
    tenant_id = uuid.uuid4()
    use_case = CreateOrderUseCase(
        order_repository=FakeOrderStore(),
        idempotency_store=InMemoryIdempotencyStore(),
        event_bus=InMemoryEventBus(),
    )

    first = await use_case.execute(
        tenant_id=tenant_id, order_type=OrderType.TABLE, items=_items(), idempotency_key="key-1"
    )
    second = await use_case.execute(
        tenant_id=tenant_id, order_type=OrderType.TABLE, items=_items(), idempotency_key="key-1"
    )

    assert first.id == second.id


@pytest.mark.asyncio
async def test_create_order_without_idempotency_key_always_creates_a_new_order() -> None:
    tenant_id = uuid.uuid4()
    use_case = CreateOrderUseCase(
        order_repository=FakeOrderStore(),
        idempotency_store=InMemoryIdempotencyStore(),
        event_bus=InMemoryEventBus(),
    )

    first = await use_case.execute(tenant_id=tenant_id, order_type=OrderType.TABLE, items=_items())
    second = await use_case.execute(tenant_id=tenant_id, order_type=OrderType.TABLE, items=_items())

    assert first.id != second.id
