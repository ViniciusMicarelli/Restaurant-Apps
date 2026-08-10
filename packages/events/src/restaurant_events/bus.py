"""EventBus: abstração de publicação/consumo de eventos de domínio.

Duas implementações:
- `InMemoryEventBus`: sem infraestrutura externa, usada em testes unitários
  e scripts locais.
- `RabbitMQEventBus`: implementação real sobre RabbitMQ (`aio-pika`), usada
  em dev/prod para a Saga por coreografia entre `order-service`,
  `inventory-service`, `kitchen-service`, `payment-service`, etc.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Protocol

import aio_pika
from aio_pika.abc import (
    AbstractChannel,
    AbstractExchange,
    AbstractIncomingMessage,
    AbstractRobustConnection,
)

from restaurant_events.envelope import DomainEvent

EventHandler = Callable[[DomainEvent], Awaitable[None]]


class EventBus(Protocol):
    """Contrato mínimo que qualquer implementação de barramento de eventos deve seguir."""

    async def publish(self, event: DomainEvent, *, routing_key: str) -> None: ...

    async def subscribe(
        self, routing_key: str, handler: EventHandler, *, queue_name: str | None = None
    ) -> None: ...


class InMemoryEventBus:
    """Barramento de eventos em memória — sem broker externo (testes/scripts locais)."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = {}
        self.published: list[tuple[str, DomainEvent]] = []

    async def publish(self, event: DomainEvent, *, routing_key: str) -> None:
        self.published.append((routing_key, event))
        for handler in self._handlers.get(routing_key, []):
            await handler(event)

    async def subscribe(
        self, routing_key: str, handler: EventHandler, *, queue_name: str | None = None
    ) -> None:
        del queue_name  # irrelevante em memória: cada handler já é independente
        self._handlers.setdefault(routing_key, []).append(handler)


class RabbitMQEventBus:
    """Barramento de eventos real sobre RabbitMQ, usando um exchange `topic` durável."""

    EXCHANGE_NAME = "restaurant.domain_events"

    def __init__(self, amqp_url: str) -> None:
        self._amqp_url = amqp_url
        self._connection: AbstractRobustConnection | None = None
        self._channel: AbstractChannel | None = None
        self._exchange: AbstractExchange | None = None

    async def connect(self) -> None:
        """Abre a conexão robusta, o canal e declara o exchange de eventos de domínio."""
        self._connection = await aio_pika.connect_robust(self._amqp_url)
        self._channel = await self._connection.channel()
        self._exchange = await self._channel.declare_exchange(
            self.EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC, durable=True
        )

    async def close(self) -> None:
        """Encerra a conexão com o RabbitMQ, se estiver aberta."""
        if self._connection is not None:
            await self._connection.close()

    async def publish(self, event: DomainEvent, *, routing_key: str) -> None:
        if self._exchange is None:
            raise RuntimeError("RabbitMQEventBus.connect() deve ser chamado antes de publish().")

        message = aio_pika.Message(
            body=event.model_dump_json().encode("utf-8"),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )
        await self._exchange.publish(message, routing_key=routing_key)

    async def subscribe(
        self, routing_key: str, handler: EventHandler, *, queue_name: str | None = None
    ) -> None:
        """Assina `routing_key`, processando mensagens com `handler`.

        `queue_name` DEVE ser exclusivo por serviço consumidor quando mais de
        um serviço assina a mesma `routing_key` (ex: `order.created` é
        consumido por `kitchen-service` E `inventory-service`). Sem isso, o
        nome padrão (`f"{routing_key}.queue"`) faz os dois se ligarem à MESMA
        fila do RabbitMQ — o broker então distribui cada mensagem para só UM
        dos consumidores concorrentes (round-robin), quebrando silenciosamente
        o fan-out da Saga por coreografia (ADR-001): o segundo serviço nunca
        recebe o evento. Prefixe com o nome do serviço, ex:
        `queue_name="kitchen-service.order.created"`.
        """
        if self._channel is None or self._exchange is None:
            raise RuntimeError("RabbitMQEventBus.connect() deve ser chamado antes de subscribe().")

        resolved_queue_name = queue_name or f"{routing_key}.queue"
        queue = await self._channel.declare_queue(resolved_queue_name, durable=True)
        await queue.bind(self._exchange, routing_key=routing_key)

        async def _on_message(message: AbstractIncomingMessage) -> None:
            async with message.process():
                event = DomainEvent.model_validate_json(message.body)
                await handler(event)

        await queue.consume(_on_message)
