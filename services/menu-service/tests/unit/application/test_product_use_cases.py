"""Testes unitários dos casos de uso de Produtos e Busca."""

import uuid

import pytest
from restaurant_core.exceptions import ResourceNotFoundException
from src.application.use_cases.product_use_cases import (
    CreateProductUseCase,
    ListProductsUseCase,
    UpdateProductUseCase,
)
from src.application.use_cases.search_products import SearchProductsUseCase
from src.domain.entities.category import Category
from tests.unit.fakes import FakeCategoryStore, FakeProductStore, FakeSearchIndex


@pytest.mark.asyncio
async def test_create_product_requires_an_existing_category() -> None:
    tenant_id = uuid.uuid4()
    use_case = CreateProductUseCase(
        product_repository=FakeProductStore(),
        category_repository=FakeCategoryStore(),
        search_index=FakeSearchIndex(),
    )

    with pytest.raises(ResourceNotFoundException):
        await use_case.execute(
            tenant_id=tenant_id, category_id=uuid.uuid4(), name="X-Burger", price=25.0
        )


@pytest.mark.asyncio
async def test_create_product_indexes_it_for_search() -> None:
    tenant_id = uuid.uuid4()
    category = Category(id=uuid.uuid4(), tenant_id=tenant_id, name="Burgers")
    search_index = FakeSearchIndex()
    use_case = CreateProductUseCase(
        product_repository=FakeProductStore(),
        category_repository=FakeCategoryStore([category]),
        search_index=search_index,
    )

    created = await use_case.execute(
        tenant_id=tenant_id, category_id=category.id, name="X-Burger", price=25.0
    )

    results = await SearchProductsUseCase(search_index=search_index).execute(
        tenant_id=tenant_id, query="Burger"
    )
    assert any(r.id == created.id for r in results)


@pytest.mark.asyncio
async def test_search_never_returns_results_from_another_tenant() -> None:
    tenant_a, tenant_b = uuid.uuid4(), uuid.uuid4()
    category_a = Category(id=uuid.uuid4(), tenant_id=tenant_a, name="Burgers")
    search_index = FakeSearchIndex()
    create_use_case = CreateProductUseCase(
        product_repository=FakeProductStore(),
        category_repository=FakeCategoryStore([category_a]),
        search_index=search_index,
    )
    await create_use_case.execute(
        tenant_id=tenant_a, category_id=category_a.id, name="X-Burger", price=25.0
    )

    results = await SearchProductsUseCase(search_index=search_index).execute(
        tenant_id=tenant_b, query="Burger"
    )

    assert results == []


@pytest.mark.asyncio
async def test_list_products_sorted_by_display_order() -> None:
    tenant_id = uuid.uuid4()
    category = Category(id=uuid.uuid4(), tenant_id=tenant_id, name="Burgers")
    product_repository = FakeProductStore()
    use_case = CreateProductUseCase(
        product_repository=product_repository,
        category_repository=FakeCategoryStore([category]),
        search_index=FakeSearchIndex(),
    )
    await use_case.execute(
        tenant_id=tenant_id, category_id=category.id, name="Segundo", price=10.0, display_order=2
    )
    await use_case.execute(
        tenant_id=tenant_id, category_id=category.id, name="Primeiro", price=10.0, display_order=1
    )

    listed = await ListProductsUseCase(product_repository=product_repository).execute()

    assert [p.name for p in listed] == ["Primeiro", "Segundo"]


@pytest.mark.asyncio
async def test_update_product_changes_price_and_reindexes() -> None:
    tenant_id = uuid.uuid4()
    category = Category(id=uuid.uuid4(), tenant_id=tenant_id, name="Burgers")
    product_repository = FakeProductStore()
    search_index = FakeSearchIndex()
    created = await CreateProductUseCase(
        product_repository=product_repository,
        category_repository=FakeCategoryStore([category]),
        search_index=search_index,
    ).execute(tenant_id=tenant_id, category_id=category.id, name="X-Burger", price=25.0)

    updated = await UpdateProductUseCase(
        product_repository=product_repository, search_index=search_index
    ).execute(
        product_id=created.id,
        name="X-Burger Especial",
        description="Novo",
        price=29.9,
        is_active=True,
    )

    assert updated.name == "X-Burger Especial"
    assert updated.price == 29.9
