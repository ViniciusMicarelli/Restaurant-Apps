"""Fakes em memória dos contratos do `inventory-service` — usados pelos testes unitários."""

from __future__ import annotations

import uuid

from src.domain.entities.inventory_item import InventoryItem
from src.domain.entities.recipe import Recipe
from src.domain.entities.stock_movement import StockMovement
from src.domain.entities.supplier import Supplier


class FakeInventoryItemStore:
    def __init__(self, items: list[InventoryItem] | None = None) -> None:
        self._items: dict[uuid.UUID, InventoryItem] = {i.id: i for i in (items or [])}

    async def get_by_id(self, inventory_item_id: uuid.UUID) -> InventoryItem | None:
        return self._items.get(inventory_item_id)

    async def list_all(self) -> list[InventoryItem]:
        return list(self._items.values())

    async def add(self, item: InventoryItem) -> InventoryItem:
        self._items[item.id] = item
        return item

    async def save(self, item: InventoryItem) -> InventoryItem:
        self._items[item.id] = item
        return item


class FakeSupplierStore:
    def __init__(self) -> None:
        self._suppliers: list[Supplier] = []

    async def list_all(self) -> list[Supplier]:
        return list(self._suppliers)

    async def add(self, supplier: Supplier) -> Supplier:
        self._suppliers.append(supplier)
        return supplier


class FakeRecipeStore:
    def __init__(self, recipes: list[Recipe] | None = None) -> None:
        self._recipes: dict[uuid.UUID, Recipe] = {r.id: r for r in (recipes or [])}

    async def get_by_product_id(self, product_id: uuid.UUID) -> Recipe | None:
        for recipe in self._recipes.values():
            if recipe.product_id == product_id:
                return recipe
        return None

    async def add(self, recipe: Recipe) -> Recipe:
        self._recipes[recipe.id] = recipe
        return recipe

    async def save(self, recipe: Recipe) -> Recipe:
        self._recipes[recipe.id] = recipe
        return recipe


class FakeStockMovementStore:
    def __init__(self) -> None:
        self.movements: list[StockMovement] = []

    async def add(self, movement: StockMovement) -> StockMovement:
        self.movements.append(movement)
        return movement

    async def list_by_item(self, inventory_item_id: uuid.UUID) -> list[StockMovement]:
        return [m for m in self.movements if m.inventory_item_id == inventory_item_id]
