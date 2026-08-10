"""Testes unitários dos casos de uso do `notification-service` (repositórios fake, sem DB real)."""

from __future__ import annotations

import uuid

import pytest
from restaurant_core.exceptions import ResourceNotFoundException
from restaurant_events import InMemoryEventBus
from src.application.use_cases.create_notification_template import (
    CreateNotificationTemplateUseCase,
)
from src.application.use_cases.queue_notification import (
    ListNotificationsUseCase,
    QueueNotificationUseCase,
)
from src.domain.entities.notification_template import NotificationChannel, NotificationTemplate
from src.domain.exceptions import (
    ChannelMismatchException,
    DuplicateTemplateCodeException,
    TemplateContextError,
)
from tests.unit.fakes import FakeNotificationStore, FakeTemplateStore


@pytest.mark.asyncio
async def test_create_template_persists_and_returns_response() -> None:
    tenant_id = uuid.uuid4()
    use_case = CreateNotificationTemplateUseCase(template_repository=FakeTemplateStore())

    response = await use_case.execute(
        tenant_id=tenant_id,
        code="queue_position",
        channel=NotificationChannel.WHATSAPP,
        body="Olá {nome}, sua vez está chegando!",
        subject=None,
    )

    assert response.code == "QUEUE_POSITION"


@pytest.mark.asyncio
async def test_create_template_rejects_duplicate_code() -> None:
    tenant_id = uuid.uuid4()
    store = FakeTemplateStore(
        [
            NotificationTemplate(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                code="QUEUE_POSITION",
                channel=NotificationChannel.WHATSAPP,
                body="Olá {nome}.",
            )
        ]
    )
    use_case = CreateNotificationTemplateUseCase(template_repository=store)

    with pytest.raises(DuplicateTemplateCodeException):
        await use_case.execute(
            tenant_id=tenant_id,
            code="queue_position",
            channel=NotificationChannel.WHATSAPP,
            body="Outro corpo {nome}.",
            subject=None,
        )


@pytest.mark.asyncio
async def test_queue_notification_persists_and_publishes_event() -> None:
    tenant_id = uuid.uuid4()
    template = NotificationTemplate(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        code="QUEUE_POSITION",
        channel=NotificationChannel.WHATSAPP,
        body="Olá {nome}, sua posição é {posicao}.",
    )
    event_bus = InMemoryEventBus()
    use_case = QueueNotificationUseCase(
        notification_repository=FakeNotificationStore(),
        template_repository=FakeTemplateStore([template]),
        event_bus=event_bus,
    )

    response = await use_case.execute(
        tenant_id=tenant_id,
        channel=NotificationChannel.WHATSAPP,
        recipient="+5511999999999",
        template_code="queue_position",
        context={"nome": "Ana", "posicao": "2"},
    )

    assert response.status.value == "QUEUED"
    assert len(event_bus.published) == 1
    routing_key, event = event_bus.published[0]
    assert routing_key == "notification.requested"
    assert event.payload["recipient"] == "+5511999999999"


@pytest.mark.asyncio
async def test_queue_notification_template_not_found_raises() -> None:
    use_case = QueueNotificationUseCase(
        notification_repository=FakeNotificationStore(),
        template_repository=FakeTemplateStore(),
        event_bus=InMemoryEventBus(),
    )

    with pytest.raises(ResourceNotFoundException):
        await use_case.execute(
            tenant_id=uuid.uuid4(),
            channel=NotificationChannel.EMAIL,
            recipient="a@b.com",
            template_code="NOPE",
            context={},
        )


@pytest.mark.asyncio
async def test_queue_notification_channel_mismatch_raises() -> None:
    tenant_id = uuid.uuid4()
    template = NotificationTemplate(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        code="QUEUE_POSITION",
        channel=NotificationChannel.WHATSAPP,
        body="Olá {nome}.",
    )
    use_case = QueueNotificationUseCase(
        notification_repository=FakeNotificationStore(),
        template_repository=FakeTemplateStore([template]),
        event_bus=InMemoryEventBus(),
    )

    with pytest.raises(ChannelMismatchException):
        await use_case.execute(
            tenant_id=tenant_id,
            channel=NotificationChannel.PUSH,
            recipient="device-token",
            template_code="queue_position",
            context={"nome": "Ana"},
        )


@pytest.mark.asyncio
async def test_queue_notification_missing_context_key_raises() -> None:
    tenant_id = uuid.uuid4()
    template = NotificationTemplate(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        code="QUEUE_POSITION",
        channel=NotificationChannel.WHATSAPP,
        body="Olá {nome}, sua posição é {posicao}.",
    )
    use_case = QueueNotificationUseCase(
        notification_repository=FakeNotificationStore(),
        template_repository=FakeTemplateStore([template]),
        event_bus=InMemoryEventBus(),
    )

    with pytest.raises(TemplateContextError):
        await use_case.execute(
            tenant_id=tenant_id,
            channel=NotificationChannel.WHATSAPP,
            recipient="+5511999999999",
            template_code="queue_position",
            context={"nome": "Ana"},
        )


@pytest.mark.asyncio
async def test_list_notifications_returns_all() -> None:
    tenant_id = uuid.uuid4()
    template = NotificationTemplate(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        code="QUEUE_POSITION",
        channel=NotificationChannel.WHATSAPP,
        body="Olá {nome}.",
    )
    notification_store = FakeNotificationStore()
    queue_use_case = QueueNotificationUseCase(
        notification_repository=notification_store,
        template_repository=FakeTemplateStore([template]),
        event_bus=InMemoryEventBus(),
    )
    await queue_use_case.execute(
        tenant_id=tenant_id,
        channel=NotificationChannel.WHATSAPP,
        recipient="+5511999999999",
        template_code="queue_position",
        context={"nome": "Ana"},
    )

    list_use_case = ListNotificationsUseCase(notification_repository=notification_store)
    result = await list_use_case.execute()

    assert len(result) == 1
