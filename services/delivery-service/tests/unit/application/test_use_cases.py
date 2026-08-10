"""Testes unitários dos casos de uso do `delivery-service` (repositório fake, sem DB real)."""

from __future__ import annotations

import uuid

import pytest
from restaurant_core.exceptions import ResourceNotFoundException
from src.application.use_cases.create_delivery import CreateDeliveryUseCase, ListDeliveriesUseCase
from src.application.use_cases.update_delivery_status import (
    AssignCourierUseCase,
    UpdateDeliveryStatusUseCase,
)
from src.domain.entities.delivery import Delivery, DeliveryStatus
from src.domain.exceptions import InvalidDeliveryTransitionError
from tests.unit.fakes import FakeDeliveryStore


@pytest.mark.asyncio
async def test_create_delivery_persists_and_returns_response() -> None:
    tenant_id, order_id = uuid.uuid4(), uuid.uuid4()
    use_case = CreateDeliveryUseCase(delivery_repository=FakeDeliveryStore())

    response = await use_case.execute(
        tenant_id=tenant_id, order_id=order_id, delivery_address="Av. Paulista, 1000"
    )

    assert response.status == DeliveryStatus.PENDING
    assert response.order_id == order_id


@pytest.mark.asyncio
async def test_list_deliveries_returns_all() -> None:
    tenant_id = uuid.uuid4()
    store = FakeDeliveryStore(
        [
            Delivery(
                id=uuid.uuid4(), tenant_id=tenant_id, order_id=uuid.uuid4(), delivery_address="A"
            ),
            Delivery(
                id=uuid.uuid4(), tenant_id=tenant_id, order_id=uuid.uuid4(), delivery_address="B"
            ),
        ]
    )
    use_case = ListDeliveriesUseCase(delivery_repository=store)

    result = await use_case.execute()

    assert len(result) == 2


@pytest.mark.asyncio
async def test_assign_courier_updates_status_and_name() -> None:
    delivery = Delivery(
        id=uuid.uuid4(), tenant_id=uuid.uuid4(), order_id=uuid.uuid4(), delivery_address="Rua X"
    )
    use_case = AssignCourierUseCase(delivery_repository=FakeDeliveryStore([delivery]))

    response = await use_case.execute(delivery_id=delivery.id, courier_name="Maria Motogirl")

    assert response.status == DeliveryStatus.ASSIGNED
    assert response.courier_name == "Maria Motogirl"


@pytest.mark.asyncio
async def test_assign_courier_not_found_raises() -> None:
    use_case = AssignCourierUseCase(delivery_repository=FakeDeliveryStore())
    with pytest.raises(ResourceNotFoundException):
        await use_case.execute(delivery_id=uuid.uuid4(), courier_name="Maria")


@pytest.mark.asyncio
async def test_update_delivery_status_invalid_transition_raises_domain_exception() -> None:
    delivery = Delivery(
        id=uuid.uuid4(), tenant_id=uuid.uuid4(), order_id=uuid.uuid4(), delivery_address="Rua X"
    )
    use_case = UpdateDeliveryStatusUseCase(delivery_repository=FakeDeliveryStore([delivery]))

    with pytest.raises(InvalidDeliveryTransitionError):
        await use_case.execute(delivery_id=delivery.id, new_status=DeliveryStatus.DELIVERED)


@pytest.mark.asyncio
async def test_update_delivery_status_valid_transition() -> None:
    delivery = Delivery(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        order_id=uuid.uuid4(),
        delivery_address="Rua X",
        status=DeliveryStatus.ASSIGNED,
    )
    use_case = UpdateDeliveryStatusUseCase(delivery_repository=FakeDeliveryStore([delivery]))

    response = await use_case.execute(delivery_id=delivery.id, new_status=DeliveryStatus.IN_TRANSIT)

    assert response.status == DeliveryStatus.IN_TRANSIT
