"""Contratos de repositório do cardápio (Repository Pattern com Interfaces)."""

from __future__ import annotations

import uuid
from typing import Protocol

from src.domain.entities.addon import AddonGroup
from src.domain.entities.category import Category
from src.domain.entities.product import Product


class CategoryRepositoryInterface(Protocol):
    async def get_by_id(self, category_id: uuid.UUID) -> Category | None: ...

    async def list_all(self) -> list[Category]: ...

    async def add(self, category: Category) -> Category: ...


class ProductRepositoryInterface(Protocol):
    async def get_by_id(self, product_id: uuid.UUID) -> Product | None: ...

    async def list_by_category(self, category_id: uuid.UUID) -> list[Product]: ...

    async def list_all(self) -> list[Product]: ...

    async def add(self, product: Product) -> Product: ...

    async def save(self, product: Product) -> Product: ...


class AddonGroupRepositoryInterface(Protocol):
    async def list_by_product(self, product_id: uuid.UUID) -> list[AddonGroup]: ...

    async def add(self, addon_group: AddonGroup) -> AddonGroup: ...
