"""Testes unitários dos casos de uso do `inventory-service` (repositórios fake, sem DB real)."""

from __future__ import annotations

import uuid

import pytest
from restaurant_core.exceptions import ResourceNotFoundException
from src.application.dtos.inventory_dtos import RecipeItemRequest
from src.application.use_cases.adjust_stock_count import AdjustStockCountUseCase
from src.application.use_cases.create_inventory_item import CreateInventoryItemUseCase
from src.application.use_cases.create_supplier import CreateSupplierUseCase, ListSuppliersUseCase
from src.application.use_cases.deduct_stock_for_order import DeductStockForOrderUseCase
from src.application.use_cases.get_recipe import GetRecipeUseCase
from src.application.use_cases.list_inventory_items import ListInventoryItemsUseCase
from src.application.use_cases.register_stock_movement import RegisterStockMovementUseCase
from src.application.use_cases.upsert_recipe import UpsertRecipeUseCase
from src.domain.entities.inventory_item import InventoryItem, InventoryUnit
from src.domain.entities.recipe import Recipe, RecipeItem
from src.domain.entities.stock_movement import StockMovementType
from src.domain.exceptions import InsufficientStockException
from tests.unit.fakes import (
    FakeInventoryItemStore,
    FakeRecipeStore,
    FakeStockMovementStore,
    FakeSupplierStore,
)


@pytest.mark.asyncio
async def test_create_inventory_item_persists_and_returns_response() -> None:
    tenant_id = uuid.uuid4()
    store = FakeInventoryItemStore()
    use_case = CreateInventoryItemUseCase(inventory_item_repository=store)

    response = await use_case.execute(
        tenant_id=tenant_id,
        name="Queijo Cheddar",
        unit=InventoryUnit.KG,
        initial_quantity=10.0,
        minimum_quantity=2.0,
        supplier_id=None,
    )

    assert response.name == "Queijo Cheddar"
    assert response.is_below_minimum is False


@pytest.mark.asyncio
async def test_list_inventory_items_filters_below_minimum() -> None:
    tenant_id = uuid.uuid4()
    low_item = InventoryItem(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        name="Alface",
        unit=InventoryUnit.UN,
        current_quantity=1.0,
        minimum_quantity=5.0,
    )
    ok_item = InventoryItem(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        name="Tomate",
        unit=InventoryUnit.UN,
        current_quantity=20.0,
        minimum_quantity=5.0,
    )
    store = FakeInventoryItemStore([low_item, ok_item])
    use_case = ListInventoryItemsUseCase(inventory_item_repository=store)

    result = await use_case.execute(only_below_minimum=True)

    assert len(result) == 1
    assert result[0].name == "Alface"


@pytest.mark.asyncio
async def test_register_stock_movement_entry_increases_quantity() -> None:
    item = InventoryItem(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        name="Pão",
        unit=InventoryUnit.UN,
        current_quantity=10.0,
    )
    item_store = FakeInventoryItemStore([item])
    movement_store = FakeStockMovementStore()
    use_case = RegisterStockMovementUseCase(
        inventory_item_repository=item_store, stock_movement_repository=movement_store
    )

    response = await use_case.execute(
        inventory_item_id=item.id,
        movement_type=StockMovementType.ENTRY,
        quantity=5.0,
        reason="Compra",
    )

    assert response.quantity_delta == 5.0
    assert item.current_quantity == 15.0
    assert len(movement_store.movements) == 1


@pytest.mark.asyncio
async def test_register_stock_movement_loss_raises_when_insufficient() -> None:
    item = InventoryItem(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        name="Pão",
        unit=InventoryUnit.UN,
        current_quantity=2.0,
    )
    use_case = RegisterStockMovementUseCase(
        inventory_item_repository=FakeInventoryItemStore([item]),
        stock_movement_repository=FakeStockMovementStore(),
    )

    with pytest.raises(InsufficientStockException):
        await use_case.execute(
            inventory_item_id=item.id,
            movement_type=StockMovementType.LOSS,
            quantity=5.0,
            reason=None,
        )


@pytest.mark.asyncio
async def test_register_stock_movement_not_found_raises() -> None:
    use_case = RegisterStockMovementUseCase(
        inventory_item_repository=FakeInventoryItemStore(),
        stock_movement_repository=FakeStockMovementStore(),
    )

    with pytest.raises(ResourceNotFoundException):
        await use_case.execute(
            inventory_item_id=uuid.uuid4(),
            movement_type=StockMovementType.ENTRY,
            quantity=1.0,
            reason=None,
        )


@pytest.mark.asyncio
async def test_adjust_stock_count_updates_quantity_and_logs_delta() -> None:
    item = InventoryItem(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        name="Pão",
        unit=InventoryUnit.UN,
        current_quantity=10.0,
    )
    movement_store = FakeStockMovementStore()
    use_case = AdjustStockCountUseCase(
        inventory_item_repository=FakeInventoryItemStore([item]),
        stock_movement_repository=movement_store,
    )

    response = await use_case.execute(
        inventory_item_id=item.id, counted_quantity=7.0, reason="Contagem mensal"
    )

    assert response.quantity_delta == -3.0
    assert item.current_quantity == 7.0
    assert movement_store.movements[0].movement_type == StockMovementType.COUNT_ADJUSTMENT


@pytest.mark.asyncio
async def test_create_and_list_suppliers() -> None:
    tenant_id = uuid.uuid4()
    store = FakeSupplierStore()
    create_use_case = CreateSupplierUseCase(supplier_repository=store)
    await create_use_case.execute(
        tenant_id=tenant_id, name="Distribuidora ABC", contact_phone=None, contact_email=None
    )

    list_use_case = ListSuppliersUseCase(supplier_repository=store)
    result = await list_use_case.execute()

    assert len(result) == 1
    assert result[0].name == "Distribuidora ABC"


@pytest.mark.asyncio
async def test_upsert_recipe_creates_when_not_existing() -> None:
    tenant_id, product_id = uuid.uuid4(), uuid.uuid4()
    store = FakeRecipeStore()
    use_case = UpsertRecipeUseCase(recipe_repository=store)

    response = await use_case.execute(
        tenant_id=tenant_id,
        product_id=product_id,
        items=[RecipeItemRequest(inventory_item_id=uuid.uuid4(), quantity_required=2.0)],
    )

    assert response.product_id == product_id
    assert len(response.items) == 1


@pytest.mark.asyncio
async def test_upsert_recipe_replaces_items_when_existing() -> None:
    tenant_id, product_id = uuid.uuid4(), uuid.uuid4()
    existing = Recipe(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        product_id=product_id,
        items=[RecipeItem(inventory_item_id=uuid.uuid4(), quantity_required=1.0)],
    )
    store = FakeRecipeStore([existing])
    use_case = UpsertRecipeUseCase(recipe_repository=store)

    new_inventory_item_id = uuid.uuid4()
    response = await use_case.execute(
        tenant_id=tenant_id,
        product_id=product_id,
        items=[RecipeItemRequest(inventory_item_id=new_inventory_item_id, quantity_required=5.0)],
    )

    assert response.id == existing.id
    assert len(response.items) == 1
    assert response.items[0].inventory_item_id == new_inventory_item_id


@pytest.mark.asyncio
async def test_get_recipe_not_found_raises() -> None:
    use_case = GetRecipeUseCase(recipe_repository=FakeRecipeStore())

    with pytest.raises(ResourceNotFoundException):
        await use_case.execute(product_id=uuid.uuid4())


@pytest.mark.asyncio
async def test_deduct_stock_for_order_applies_recipe_deduction() -> None:
    tenant_id, order_id, product_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    inventory_item = InventoryItem(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        name="Pão",
        unit=InventoryUnit.UN,
        current_quantity=100.0,
    )
    recipe = Recipe(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        product_id=product_id,
        items=[RecipeItem(inventory_item_id=inventory_item.id, quantity_required=2.0)],
    )
    item_store = FakeInventoryItemStore([inventory_item])
    recipe_store = FakeRecipeStore([recipe])
    movement_store = FakeStockMovementStore()
    use_case = DeductStockForOrderUseCase(
        inventory_item_repository=item_store,
        recipe_repository=recipe_store,
        stock_movement_repository=movement_store,
    )

    await use_case.execute(
        tenant_id=tenant_id,
        order_id=order_id,
        items=[{"product_id": str(product_id), "quantity": 3}],
    )

    assert inventory_item.current_quantity == 94.0  # 100 - (2 * 3)
    assert len(movement_store.movements) == 1
    assert movement_store.movements[0].movement_type == StockMovementType.SALE_DEDUCTION
    assert movement_store.movements[0].order_id == order_id


@pytest.mark.asyncio
async def test_deduct_stock_for_order_skips_products_without_recipe() -> None:
    tenant_id, order_id = uuid.uuid4(), uuid.uuid4()
    movement_store = FakeStockMovementStore()
    use_case = DeductStockForOrderUseCase(
        inventory_item_repository=FakeInventoryItemStore(),
        recipe_repository=FakeRecipeStore(),
        stock_movement_repository=movement_store,
    )

    await use_case.execute(
        tenant_id=tenant_id,
        order_id=order_id,
        items=[{"product_id": str(uuid.uuid4()), "quantity": 1}],
    )

    assert movement_store.movements == []


@pytest.mark.asyncio
async def test_deduct_stock_for_order_allows_negative_stock() -> None:
    tenant_id, order_id, product_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    inventory_item = InventoryItem(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        name="Pão",
        unit=InventoryUnit.UN,
        current_quantity=1.0,
    )
    recipe = Recipe(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        product_id=product_id,
        items=[RecipeItem(inventory_item_id=inventory_item.id, quantity_required=5.0)],
    )
    use_case = DeductStockForOrderUseCase(
        inventory_item_repository=FakeInventoryItemStore([inventory_item]),
        recipe_repository=FakeRecipeStore([recipe]),
        stock_movement_repository=FakeStockMovementStore(),
    )

    await use_case.execute(
        tenant_id=tenant_id,
        order_id=order_id,
        items=[{"product_id": str(product_id), "quantity": 1}],
    )

    assert inventory_item.current_quantity == -4.0
