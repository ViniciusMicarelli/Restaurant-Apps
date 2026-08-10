"""Testes unitários dos casos de uso de Mesas."""

import uuid

import pytest
from restaurant_core.exceptions import ResourceNotFoundException
from src.application.use_cases.table_use_cases import (
    CreateTableUseCase,
    ListTablesUseCase,
    MarkTableCleanedUseCase,
)
from src.domain.entities.table import Table, TableStatus
from src.domain.exceptions import DuplicateTableNumberError, TableNotAwaitingCleaningError
from tests.unit.fakes import FakeTableStore


@pytest.mark.asyncio
async def test_create_table_persists_with_default_status_available() -> None:
    store = FakeTableStore()
    use_case = CreateTableUseCase(table_repository=store)

    response = await use_case.execute(tenant_id=uuid.uuid4(), number=1, capacity=4)

    assert response.status.value == "AVAILABLE"


@pytest.mark.asyncio
async def test_create_table_rejects_duplicate_number() -> None:
    tenant_id = uuid.uuid4()
    store = FakeTableStore()
    use_case = CreateTableUseCase(table_repository=store)
    await use_case.execute(tenant_id=tenant_id, number=1, capacity=4)

    with pytest.raises(DuplicateTableNumberError):
        await use_case.execute(tenant_id=tenant_id, number=1, capacity=2)


@pytest.mark.asyncio
async def test_list_tables_sorted_by_number() -> None:
    tenant_id = uuid.uuid4()
    store = FakeTableStore()
    use_case = CreateTableUseCase(table_repository=store)
    await use_case.execute(tenant_id=tenant_id, number=3, capacity=4)
    await use_case.execute(tenant_id=tenant_id, number=1, capacity=2)

    listed = await ListTablesUseCase(table_repository=store).execute()

    assert [t.number for t in listed] == [1, 3]


@pytest.mark.asyncio
async def test_mark_table_cleaned_releases_waiting_cleaning_table_to_available() -> None:
    table = Table(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        number=5,
        capacity=4,
        status=TableStatus.WAITING_CLEANING,
    )
    store = FakeTableStore([table])

    response = await MarkTableCleanedUseCase(table_repository=store).execute(table_id=table.id)

    assert response.status == TableStatus.AVAILABLE


@pytest.mark.asyncio
async def test_mark_table_cleaned_rejects_table_not_awaiting_cleaning() -> None:
    table = Table(
        id=uuid.uuid4(), tenant_id=uuid.uuid4(), number=5, capacity=4, status=TableStatus.OCCUPIED
    )
    store = FakeTableStore([table])

    with pytest.raises(TableNotAwaitingCleaningError):
        await MarkTableCleanedUseCase(table_repository=store).execute(table_id=table.id)


@pytest.mark.asyncio
async def test_mark_table_cleaned_raises_not_found_for_unknown_table() -> None:
    store = FakeTableStore()

    with pytest.raises(ResourceNotFoundException):
        await MarkTableCleanedUseCase(table_repository=store).execute(table_id=uuid.uuid4())
