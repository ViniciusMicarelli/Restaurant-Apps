"""Testes do `EventBus`: implementação em memória e guard clauses do RabbitMQEventBus."""

import uuid

import pytest
from restaurant_events.bus import InMemoryEventBus, RabbitMQEventBus
from restaurant_events.envelope import DomainEvent


@pytest.mark.asyncio
async def test_in_memory_event_bus_delivers_published_event_to_subscribed_handler() -> None:
    bus = InMemoryEventBus()
    received: list[DomainEvent] = []

    async def _handler(event: DomainEvent) -> None:
        received.append(event)

    await bus.subscribe("order.created", _handler)
    event = DomainEvent(
        event_type="order.created", tenant_id=uuid.uuid4(), payload={"order_id": "abc"}
    )
    await bus.publish(event, routing_key="order.created")

    assert received == [event]
    assert bus.published == [("order.created", event)]


@pytest.mark.asyncio
async def test_in_memory_event_bus_does_not_deliver_to_handlers_of_other_routing_keys() -> None:
    bus = InMemoryEventBus()
    received: list[DomainEvent] = []

    async def _handler(event: DomainEvent) -> None:
        received.append(event)

    await bus.subscribe("payment.failed", _handler)
    event = DomainEvent(event_type="order.created", tenant_id=uuid.uuid4())
    await bus.publish(event, routing_key="order.created")

    assert received == []


@pytest.mark.asyncio
async def test_rabbitmq_event_bus_publish_requires_connect_first() -> None:
    bus = RabbitMQEventBus("amqp://guest:guest@localhost:5672/")
    event = DomainEvent(event_type="order.created", tenant_id=uuid.uuid4())

    with pytest.raises(RuntimeError, match="connect"):
        await bus.publish(event, routing_key="order.created")


@pytest.mark.asyncio
async def test_rabbitmq_event_bus_subscribe_requires_connect_first() -> None:
    bus = RabbitMQEventBus("amqp://guest:guest@localhost:5672/")

    async def _handler(_event: DomainEvent) -> None:
        return None

    with pytest.raises(RuntimeError, match="connect"):
        await bus.subscribe("order.created", _handler)


@pytest.mark.asyncio
async def test_in_memory_event_bus_delivers_to_multiple_independent_subscribers() -> None:
    """Dois serviços distintos assinando a mesma routing_key (ex: `order.created`
    consumido por `kitchen-service` E `inventory-service`) devem AMBOS receber
    o evento — a fila compartilhada é justamente o bug real que motivou o
    parâmetro `queue_name` no `RabbitMQEventBus` (ver docstring de `subscribe`)."""
    bus = InMemoryEventBus()
    received_by_kitchen: list[DomainEvent] = []
    received_by_inventory: list[DomainEvent] = []

    async def _kitchen_handler(event: DomainEvent) -> None:
        received_by_kitchen.append(event)

    async def _inventory_handler(event: DomainEvent) -> None:
        received_by_inventory.append(event)

    await bus.subscribe(
        "order.created", _kitchen_handler, queue_name="kitchen-service.order.created"
    )
    await bus.subscribe(
        "order.created", _inventory_handler, queue_name="inventory-service.order.created"
    )
    event = DomainEvent(event_type="order.created", tenant_id=uuid.uuid4())
    await bus.publish(event, routing_key="order.created")

    assert received_by_kitchen == [event]
    assert received_by_inventory == [event]
