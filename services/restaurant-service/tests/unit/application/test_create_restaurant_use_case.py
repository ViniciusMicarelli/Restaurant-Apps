"""Testes unitários de `CreateRestaurantUseCase`."""

import pytest
from src.application.use_cases.create_restaurant import CreateRestaurantUseCase
from src.domain.exceptions import DuplicateSlugError
from tests.unit.fakes import FakeRestaurantStore


@pytest.mark.asyncio
async def test_create_restaurant_persists_with_default_branding() -> None:
    store = FakeRestaurantStore()
    use_case = CreateRestaurantUseCase(restaurant_repository=store)

    response = await use_case.execute(
        slug="burger-house",
        trade_name="Burger House",
        legal_name="Burger House Ltda",
        cnpj="12.345.678/0001-90",
        phone="(11) 99999-8888",
    )

    assert response.slug == "burger-house"
    assert response.currency == "BRL"
    assert response.branding.primary_color == "#EA1D2C"


@pytest.mark.asyncio
async def test_create_restaurant_rejects_duplicate_slug() -> None:
    store = FakeRestaurantStore()
    use_case = CreateRestaurantUseCase(restaurant_repository=store)

    await use_case.execute(
        slug="burger-house",
        trade_name="Burger House",
        legal_name="Burger House Ltda",
        cnpj="12.345.678/0001-90",
        phone="(11) 99999-8888",
    )

    with pytest.raises(DuplicateSlugError):
        await use_case.execute(
            slug="burger-house",
            trade_name="Outro Nome",
            legal_name="Outra Ltda",
            cnpj="99.888.777/0001-11",
            phone="(11) 91111-2222",
        )
