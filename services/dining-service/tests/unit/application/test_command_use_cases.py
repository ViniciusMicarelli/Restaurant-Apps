"""Testes unitários dos casos de uso de Comandas."""

import uuid

import pytest
from restaurant_core.exceptions import ResourceNotFoundException
from src.application.use_cases.command_use_cases import (
    CloseCommandUseCase,
    CustomerCloseCommandUseCase,
    GetOpenCommandForTableUseCase,
    OpenCommandUseCase,
)
from src.domain.entities.table import Table, TableStatus
from src.domain.exceptions import InvalidOrExpiredQrSecretError, TableNotAvailableError
from tests.unit.fakes import FakeCommandStore, FakeTableStore


@pytest.mark.asyncio
async def test_open_command_transitions_table_to_occupied() -> None:
    tenant_id = uuid.uuid4()
    table = Table(id=uuid.uuid4(), tenant_id=tenant_id, number=5, capacity=4)
    table_store = FakeTableStore([table])
    command_store = FakeCommandStore()
    use_case = OpenCommandUseCase(command_repository=command_store, table_repository=table_store)

    response = await use_case.execute(
        tenant_id=tenant_id, table_number=5, customer_name="Lucas", waiter_id=uuid.uuid4()
    )

    assert response.status.value == "OPEN"
    updated_table = await table_store.get_by_id(table.id)
    assert updated_table is not None
    assert updated_table.status == TableStatus.OCCUPIED


@pytest.mark.asyncio
async def test_open_command_rejects_unavailable_table() -> None:
    tenant_id = uuid.uuid4()
    table = Table(
        id=uuid.uuid4(), tenant_id=tenant_id, number=5, capacity=4, status=TableStatus.OCCUPIED
    )
    use_case = OpenCommandUseCase(
        command_repository=FakeCommandStore(), table_repository=FakeTableStore([table])
    )

    with pytest.raises(TableNotAvailableError):
        await use_case.execute(
            tenant_id=tenant_id, table_number=5, customer_name="Lucas", waiter_id=uuid.uuid4()
        )


@pytest.mark.asyncio
async def test_open_command_raises_not_found_for_unknown_table_number() -> None:
    use_case = OpenCommandUseCase(
        command_repository=FakeCommandStore(), table_repository=FakeTableStore()
    )

    with pytest.raises(ResourceNotFoundException):
        await use_case.execute(
            tenant_id=uuid.uuid4(), table_number=99, customer_name="Lucas", waiter_id=uuid.uuid4()
        )


@pytest.mark.asyncio
async def test_close_command_releases_table_to_waiting_cleaning() -> None:
    tenant_id = uuid.uuid4()
    table = Table(
        id=uuid.uuid4(), tenant_id=tenant_id, number=5, capacity=4, status=TableStatus.AVAILABLE
    )
    table_store = FakeTableStore([table])
    command_store = FakeCommandStore()
    open_use_case = OpenCommandUseCase(
        command_repository=command_store, table_repository=table_store
    )
    opened = await open_use_case.execute(
        tenant_id=tenant_id, table_number=5, customer_name="Lucas", waiter_id=uuid.uuid4()
    )

    close_use_case = CloseCommandUseCase(
        command_repository=command_store, table_repository=table_store
    )
    response = await close_use_case.execute(command_id=opened.id)

    assert response.status.value == "CLOSED"
    updated_table = await table_store.get_by_id(table.id)
    assert updated_table is not None
    assert updated_table.status == TableStatus.WAITING_CLEANING


@pytest.mark.asyncio
async def test_close_command_rotates_table_qr_secret() -> None:
    """Encerrar a comanda deve invalidar a secret usada durante o ciclo que
    acabou — impede que alguém que já saiu reaproveite o link do cardápio
    quando outro grupo sentar na mesma mesa."""
    tenant_id = uuid.uuid4()
    table = Table(
        id=uuid.uuid4(), tenant_id=tenant_id, number=5, capacity=4, status=TableStatus.AVAILABLE
    )
    table.rotate_qr_secret()
    previous_secret = table.active_qr_secret
    assert previous_secret is not None

    table_store = FakeTableStore([table])
    command_store = FakeCommandStore()
    open_use_case = OpenCommandUseCase(
        command_repository=command_store, table_repository=table_store
    )
    opened = await open_use_case.execute(
        tenant_id=tenant_id, table_number=5, customer_name="Lucas", waiter_id=uuid.uuid4()
    )

    close_use_case = CloseCommandUseCase(
        command_repository=command_store, table_repository=table_store
    )
    await close_use_case.execute(command_id=opened.id)

    updated_table = await table_store.get_by_id(table.id)
    assert updated_table is not None
    assert updated_table.active_qr_secret != previous_secret
    assert not updated_table.is_qr_secret_valid(previous_secret)


@pytest.mark.asyncio
async def test_get_open_command_for_table_returns_command_with_valid_secret() -> None:
    tenant_id = uuid.uuid4()
    table = Table(id=uuid.uuid4(), tenant_id=tenant_id, number=5, capacity=4)
    table.rotate_qr_secret()
    secret = table.active_qr_secret
    assert secret is not None
    table_store = FakeTableStore([table])
    command_store = FakeCommandStore()
    opened = await OpenCommandUseCase(
        command_repository=command_store, table_repository=table_store
    ).execute(tenant_id=tenant_id, table_number=5, customer_name="Lucas", waiter_id=uuid.uuid4())

    use_case = GetOpenCommandForTableUseCase(
        command_repository=command_store, table_repository=table_store
    )
    response = await use_case.execute(table_number=5, secret=secret)

    assert response.id == opened.id
    assert response.status.value == "OPEN"


@pytest.mark.asyncio
async def test_get_open_command_for_table_rejects_invalid_secret() -> None:
    tenant_id = uuid.uuid4()
    table = Table(id=uuid.uuid4(), tenant_id=tenant_id, number=5, capacity=4)
    table.rotate_qr_secret()
    table_store = FakeTableStore([table])
    use_case = GetOpenCommandForTableUseCase(
        command_repository=FakeCommandStore(), table_repository=table_store
    )

    with pytest.raises(InvalidOrExpiredQrSecretError):
        await use_case.execute(table_number=5, secret="secret-errada")


@pytest.mark.asyncio
async def test_get_open_command_for_table_raises_not_found_without_open_command() -> None:
    tenant_id = uuid.uuid4()
    table = Table(id=uuid.uuid4(), tenant_id=tenant_id, number=5, capacity=4)
    table.rotate_qr_secret()
    secret = table.active_qr_secret
    assert secret is not None
    table_store = FakeTableStore([table])
    use_case = GetOpenCommandForTableUseCase(
        command_repository=FakeCommandStore(), table_repository=table_store
    )

    with pytest.raises(ResourceNotFoundException):
        await use_case.execute(table_number=5, secret=secret)


@pytest.mark.asyncio
async def test_customer_close_command_closes_with_valid_table_secret() -> None:
    tenant_id = uuid.uuid4()
    table = Table(id=uuid.uuid4(), tenant_id=tenant_id, number=5, capacity=4)
    table.rotate_qr_secret()
    secret = table.active_qr_secret
    assert secret is not None
    table_store = FakeTableStore([table])
    command_store = FakeCommandStore()
    opened = await OpenCommandUseCase(
        command_repository=command_store, table_repository=table_store
    ).execute(tenant_id=tenant_id, table_number=5, customer_name="Lucas", waiter_id=uuid.uuid4())

    use_case = CustomerCloseCommandUseCase(
        command_repository=command_store, table_repository=table_store
    )
    response = await use_case.execute(command_id=opened.id, secret=secret)

    assert response.status.value == "CLOSED"
    updated_table = await table_store.get_by_id(table.id)
    assert updated_table is not None
    assert updated_table.status == TableStatus.WAITING_CLEANING


@pytest.mark.asyncio
async def test_customer_close_command_rejects_invalid_secret() -> None:
    tenant_id = uuid.uuid4()
    table = Table(id=uuid.uuid4(), tenant_id=tenant_id, number=5, capacity=4)
    table.rotate_qr_secret()
    table_store = FakeTableStore([table])
    command_store = FakeCommandStore()
    opened = await OpenCommandUseCase(
        command_repository=command_store, table_repository=table_store
    ).execute(tenant_id=tenant_id, table_number=5, customer_name="Lucas", waiter_id=uuid.uuid4())

    use_case = CustomerCloseCommandUseCase(
        command_repository=command_store, table_repository=table_store
    )

    with pytest.raises(InvalidOrExpiredQrSecretError):
        await use_case.execute(command_id=opened.id, secret="secret-errada")

    # A comanda continua aberta — a secret errada não deve ter efeito colateral algum.
    unchanged = await command_store.get_by_id(opened.id)
    assert unchanged is not None
    assert unchanged.status.value == "OPEN"


@pytest.mark.asyncio
async def test_customer_close_command_raises_not_found_for_unknown_command() -> None:
    use_case = CustomerCloseCommandUseCase(
        command_repository=FakeCommandStore(), table_repository=FakeTableStore()
    )

    with pytest.raises(ResourceNotFoundException):
        await use_case.execute(command_id=uuid.uuid4(), secret="qualquer-coisa")
