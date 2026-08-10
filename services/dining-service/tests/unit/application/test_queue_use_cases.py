"""Testes unitários dos casos de uso da Fila de Espera Virtual."""

import uuid

import pytest
from restaurant_core.exceptions import ResourceNotFoundException
from src.application.use_cases.queue_use_cases import (
    AddToQueueUseCase,
    CallNextInQueueUseCase,
    ListQueueUseCase,
)
from tests.unit.fakes import FakeQueueStore


@pytest.mark.asyncio
async def test_add_to_queue_assigns_incrementing_positions() -> None:
    tenant_id = uuid.uuid4()
    store = FakeQueueStore()
    use_case = AddToQueueUseCase(queue_repository=store)

    first = await use_case.execute(
        tenant_id=tenant_id, customer_name="Mariana", phone="11999990000", party_size=4
    )
    second = await use_case.execute(
        tenant_id=tenant_id, customer_name="Pedro", phone="11999990001", party_size=2
    )

    assert first.position == 1
    assert second.position == 2


@pytest.mark.asyncio
async def test_list_queue_returns_entries_ordered_by_position() -> None:
    tenant_id = uuid.uuid4()
    store = FakeQueueStore()
    add_use_case = AddToQueueUseCase(queue_repository=store)
    await add_use_case.execute(
        tenant_id=tenant_id, customer_name="Mariana", phone="11999990000", party_size=4
    )
    await add_use_case.execute(
        tenant_id=tenant_id, customer_name="Pedro", phone="11999990001", party_size=2
    )

    listed = await ListQueueUseCase(queue_repository=store).execute()

    assert [e.customer_name for e in listed] == ["Mariana", "Pedro"]
    assert [e.position for e in listed] == [1, 2]


@pytest.mark.asyncio
async def test_call_next_marks_first_entry_as_notified_and_removes_from_waiting_list() -> None:
    tenant_id = uuid.uuid4()
    store = FakeQueueStore()
    add_use_case = AddToQueueUseCase(queue_repository=store)
    await add_use_case.execute(
        tenant_id=tenant_id, customer_name="Mariana", phone="11999990000", party_size=4
    )
    await add_use_case.execute(
        tenant_id=tenant_id, customer_name="Pedro", phone="11999990001", party_size=2
    )

    called = await CallNextInQueueUseCase(queue_repository=store).execute()
    assert called.customer_name == "Mariana"

    remaining = await ListQueueUseCase(queue_repository=store).execute()
    assert [e.customer_name for e in remaining] == ["Pedro"]


@pytest.mark.asyncio
async def test_call_next_with_empty_queue_raises_not_found() -> None:
    with pytest.raises(ResourceNotFoundException):
        await CallNextInQueueUseCase(queue_repository=FakeQueueStore()).execute()
