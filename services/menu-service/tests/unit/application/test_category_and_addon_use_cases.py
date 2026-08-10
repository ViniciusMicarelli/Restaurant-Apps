"""Testes unitários dos casos de uso de Categorias e Grupos de Adicionais."""

import uuid

import pytest
from restaurant_core.exceptions import ResourceNotFoundException
from src.application.dtos.menu_dtos import AddonOptionRequest
from src.application.use_cases.addon_group_use_cases import CreateAddonGroupUseCase
from src.application.use_cases.category_use_cases import (
    CreateCategoryUseCase,
    ListCategoriesUseCase,
)
from src.domain.entities.product import Product
from tests.unit.fakes import FakeAddonGroupStore, FakeCategoryStore, FakeProductStore


@pytest.mark.asyncio
async def test_create_and_list_categories_sorted_by_display_order() -> None:
    tenant_id = uuid.uuid4()
    category_repository = FakeCategoryStore()
    create_use_case = CreateCategoryUseCase(category_repository=category_repository)

    await create_use_case.execute(tenant_id=tenant_id, name="Sobremesas", display_order=2)
    await create_use_case.execute(tenant_id=tenant_id, name="Lanches", display_order=1)

    listed = await ListCategoriesUseCase(category_repository=category_repository).execute()

    assert [c.name for c in listed] == ["Lanches", "Sobremesas"]


@pytest.mark.asyncio
async def test_create_addon_group_requires_an_existing_product() -> None:
    use_case = CreateAddonGroupUseCase(
        addon_group_repository=FakeAddonGroupStore(), product_repository=FakeProductStore()
    )

    with pytest.raises(ResourceNotFoundException):
        await use_case.execute(
            tenant_id=uuid.uuid4(),
            product_id=uuid.uuid4(),
            name="Ponto da carne",
            min_selections=1,
            max_selections=1,
            options=[AddonOptionRequest(name="Mal passado")],
        )


@pytest.mark.asyncio
async def test_create_addon_group_persists_options() -> None:
    tenant_id = uuid.uuid4()
    product = Product(
        id=uuid.uuid4(), tenant_id=tenant_id, category_id=uuid.uuid4(), name="X-Burger", price=25.0
    )
    use_case = CreateAddonGroupUseCase(
        addon_group_repository=FakeAddonGroupStore(), product_repository=FakeProductStore([product])
    )

    response = await use_case.execute(
        tenant_id=tenant_id,
        product_id=product.id,
        name="Ponto da carne",
        min_selections=1,
        max_selections=1,
        options=[
            AddonOptionRequest(name="Mal passado"),
            AddonOptionRequest(name="Bem passado", price_delta=0),
        ],
    )

    assert len(response.options) == 2
    assert response.options[0].name == "Mal passado"
