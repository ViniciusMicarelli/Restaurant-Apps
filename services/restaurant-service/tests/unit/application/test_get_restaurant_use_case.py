"""Testes unitários de `GetRestaurantByIdUseCase`/`GetRestaurantBySlugUseCase`."""

import uuid

import pytest
from restaurant_core.exceptions import ResourceNotFoundException
from src.application.use_cases.get_restaurant import (
    GetRestaurantByIdUseCase,
    GetRestaurantBySlugUseCase,
)
from src.domain.entities.restaurant import Restaurant
from tests.unit.fakes import FakeRestaurantStore


@pytest.mark.asyncio
async def test_get_by_id_returns_existing_restaurant() -> None:
    restaurant_id = uuid.uuid4()
    restaurant = Restaurant(
        id=restaurant_id,
        slug="burger-house",
        trade_name="Burger House",
        legal_name="Burger House Ltda",
        cnpj="12.345.678/0001-90",
        phone="(11) 99999-8888",
    )
    use_case = GetRestaurantByIdUseCase(restaurant_repository=FakeRestaurantStore([restaurant]))

    response = await use_case.execute(restaurant_id=restaurant_id)

    assert response.slug == "burger-house"


@pytest.mark.asyncio
async def test_get_by_id_raises_not_found_for_unknown_id() -> None:
    use_case = GetRestaurantByIdUseCase(restaurant_repository=FakeRestaurantStore())

    with pytest.raises(ResourceNotFoundException):
        await use_case.execute(restaurant_id=uuid.uuid4())


@pytest.mark.asyncio
async def test_get_by_slug_raises_not_found_for_unknown_slug() -> None:
    use_case = GetRestaurantBySlugUseCase(restaurant_repository=FakeRestaurantStore())

    with pytest.raises(ResourceNotFoundException):
        await use_case.execute(slug="nao-existe")
