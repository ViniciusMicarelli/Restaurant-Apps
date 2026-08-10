"""Testes unitários de `UpdateRestaurantUseCase` e `UpdateBrandingUseCase`."""

import uuid

import pytest
from restaurant_core.exceptions import TenantIsolationException
from src.application.dtos.restaurant_dtos import UpdateBrandingRequest
from src.application.use_cases.update_branding import UpdateBrandingUseCase
from src.application.use_cases.update_restaurant import UpdateRestaurantUseCase
from src.domain.entities.restaurant import Restaurant
from tests.unit.fakes import FakeRestaurantStore


def _make_restaurant(restaurant_id: uuid.UUID) -> Restaurant:
    return Restaurant(
        id=restaurant_id,
        slug="burger-house",
        trade_name="Burger House",
        legal_name="Burger House Ltda",
        cnpj="12.345.678/0001-90",
        phone="(11) 99999-8888",
    )


@pytest.mark.asyncio
async def test_update_restaurant_applies_changes_when_acting_as_own_tenant() -> None:
    restaurant_id = uuid.uuid4()
    store = FakeRestaurantStore([_make_restaurant(restaurant_id)])
    use_case = UpdateRestaurantUseCase(restaurant_repository=store)

    response = await use_case.execute(
        restaurant_id=restaurant_id,
        acting_tenant_id=restaurant_id,
        trade_name="Burger House Grill",
        phone="(11) 90000-0000",
        currency="USD",
        service_fee_percent=15.0,
    )

    assert response.trade_name == "Burger House Grill"
    assert response.currency == "USD"


@pytest.mark.asyncio
async def test_update_restaurant_rejects_updates_from_another_tenant() -> None:
    restaurant_id = uuid.uuid4()
    another_tenant_id = uuid.uuid4()
    store = FakeRestaurantStore([_make_restaurant(restaurant_id)])
    use_case = UpdateRestaurantUseCase(restaurant_repository=store)

    with pytest.raises(TenantIsolationException):
        await use_case.execute(
            restaurant_id=restaurant_id,
            acting_tenant_id=another_tenant_id,
            trade_name="Nome Hostil",
            phone="(11) 90000-0000",
            currency="USD",
            service_fee_percent=15.0,
        )


@pytest.mark.asyncio
async def test_update_branding_replaces_the_whole_branding_object() -> None:
    restaurant_id = uuid.uuid4()
    store = FakeRestaurantStore([_make_restaurant(restaurant_id)])
    use_case = UpdateBrandingUseCase(restaurant_repository=store)

    response = await use_case.execute(
        restaurant_id=restaurant_id,
        acting_tenant_id=restaurant_id,
        payload=UpdateBrandingRequest(
            primary_color="#000000",
            secondary_color="#111111",
            accent_color="#222222",
            theme_mode="dark",
        ),
    )

    assert response.branding.primary_color == "#000000"
    assert response.branding.theme_mode == "dark"


@pytest.mark.asyncio
async def test_update_branding_rejects_updates_from_another_tenant() -> None:
    restaurant_id = uuid.uuid4()
    store = FakeRestaurantStore([_make_restaurant(restaurant_id)])
    use_case = UpdateBrandingUseCase(restaurant_repository=store)

    with pytest.raises(TenantIsolationException):
        await use_case.execute(
            restaurant_id=restaurant_id,
            acting_tenant_id=uuid.uuid4(),
            payload=UpdateBrandingRequest(
                primary_color="#000000", secondary_color="#111111", accent_color="#222222"
            ),
        )
