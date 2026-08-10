"""Contratos de repositório do serviço de Estoque."""

from __future__ import annotations

import uuid
from typing import Protocol

from src.domain.entities.inventory_item import InventoryItem
from src.domain.entities.recipe import Recipe
from src.domain.entities.stock_movement import StockMovement
from src.domain.entities.supplier import Supplier


class InventoryItemRepositoryInterface(Protocol):
    async def get_by_id(self, inventory_item_id: uuid.UUID) -> InventoryItem | None: ...

    async def list_all(self) -> list[InventoryItem]: ...

    async def add(self, item: InventoryItem) -> InventoryItem: ...

    async def save(self, item: InventoryItem) -> InventoryItem: ...


class SupplierRepositoryInterface(Protocol):
    async def list_all(self) -> list[Supplier]: ...

    async def add(self, supplier: Supplier) -> Supplier: ...


class RecipeRepositoryInterface(Protocol):
    async def get_by_product_id(self, product_id: uuid.UUID) -> Recipe | None: ...

    async def add(self, recipe: Recipe) -> Recipe: ...

    async def save(self, recipe: Recipe) -> Recipe: ...


class StockMovementRepositoryInterface(Protocol):
    """Append-only — auditoria de movimentações de estoque."""

    async def add(self, movement: StockMovement) -> StockMovement: ...

    async def list_by_item(self, inventory_item_id: uuid.UUID) -> list[StockMovement]: ...
