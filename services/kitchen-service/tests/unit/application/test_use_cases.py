"""Testes unitários dos casos de uso do `kitchen-service` (repositórios fake, sem DB real)."""

from __future__ import annotations

import uuid

import pytest
from restaurant_core.exceptions import ResourceNotFoundException
from src.application.use_cases.create_kds_items_from_order import (
    CreateKDSItemsFromOrderUseCase,
)
from src.application.use_cases.list_kds_items import ListKDSItemsUseCase
from src.application.use_cases.update_kds_item_status import UpdateKDSItemStatusUseCase
from src.domain.entities.kds_item import KDSItem, KDSItemStatus, KDSStation
from src.domain.exceptions import InvalidKDSTransitionError
from tests.unit.fakes import FakeBroadcaster, FakeKDSItemStore, FakeKDSLogStore


@pytest.mark.asyncio
async def test_create_kds_items_from_order_creates_one_item_per_order_item() -> None:
    tenant_id, order_id = uuid.uuid4(), uuid.uuid4()
    store = FakeKDSItemStore()
    broadcaster = FakeBroadcaster()
    use_case = CreateKDSItemsFromOrderUseCase(kds_item_repository=store, broadcaster=broadcaster)

    result = await use_case.execute(
        tenant_id=tenant_id,
        order_id=order_id,
        table_number=5,
        items=[
            {"product_id": str(uuid.uuid4()), "product_name": "X-Burger", "quantity": 2},
            {"product_id": str(uuid.uuid4()), "product_name": "Coca-Cola", "quantity": 1},
        ],
    )

    assert len(result) == 2
    assert all(r.order_id == order_id for r in result)
    assert all(r.station == KDSStation.COZINHA_QUENTE for r in result)
    assert len(broadcaster.messages) == 2
    assert broadcaster.messages[0][1]["event"] == "KDS_ITEM_CREATED"


@pytest.mark.asyncio
async def test_list_kds_items_filters_by_station() -> None:
    tenant_id = uuid.uuid4()
    hot_item = KDSItem(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        order_id=uuid.uuid4(),
        product_id=uuid.uuid4(),
        product_name="Burger",
        station=KDSStation.COZINHA_QUENTE,
    )
    bar_item = KDSItem(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        order_id=uuid.uuid4(),
        product_id=uuid.uuid4(),
        product_name="Suco",
        station=KDSStation.BAR,
    )
    store = FakeKDSItemStore([hot_item, bar_item])
    use_case = ListKDSItemsUseCase(kds_item_repository=store)

    result = await use_case.execute(station=KDSStation.BAR)

    assert len(result) == 1
    assert result[0].product_name == "Suco"


@pytest.mark.asyncio
async def test_update_kds_item_status_valid_transition_logs_and_broadcasts() -> None:
    tenant_id = uuid.uuid4()
    item = KDSItem(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        order_id=uuid.uuid4(),
        product_id=uuid.uuid4(),
        product_name="Burger",
    )
    item_store = FakeKDSItemStore([item])
    log_store = FakeKDSLogStore()
    broadcaster = FakeBroadcaster()
    use_case = UpdateKDSItemStatusUseCase(
        kds_item_repository=item_store, kds_log_repository=log_store, broadcaster=broadcaster
    )

    result = await use_case.execute(kds_item_id=item.id, new_status=KDSItemStatus.PREPARING)

    assert result.status == KDSItemStatus.PREPARING
    assert len(log_store.logs) == 1
    assert log_store.logs[0].from_status == KDSItemStatus.PENDING
    assert log_store.logs[0].to_status == KDSItemStatus.PREPARING
    assert len(broadcaster.messages) == 1
    assert broadcaster.messages[0][1]["event"] == "KDS_ITEM_STATUS_CHANGED"


@pytest.mark.asyncio
async def test_update_kds_item_status_invalid_transition_raises_domain_exception() -> None:
    item = KDSItem(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        order_id=uuid.uuid4(),
        product_id=uuid.uuid4(),
        product_name="Burger",
    )
    use_case = UpdateKDSItemStatusUseCase(
        kds_item_repository=FakeKDSItemStore([item]),
        kds_log_repository=FakeKDSLogStore(),
        broadcaster=FakeBroadcaster(),
    )

    with pytest.raises(InvalidKDSTransitionError):
        await use_case.execute(kds_item_id=item.id, new_status=KDSItemStatus.READY)


@pytest.mark.asyncio
async def test_update_kds_item_status_not_found_raises_not_found() -> None:
    use_case = UpdateKDSItemStatusUseCase(
        kds_item_repository=FakeKDSItemStore(),
        kds_log_repository=FakeKDSLogStore(),
        broadcaster=FakeBroadcaster(),
    )

    with pytest.raises(ResourceNotFoundException):
        await use_case.execute(kds_item_id=uuid.uuid4(), new_status=KDSItemStatus.PREPARING)
