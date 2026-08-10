"""Fakes em memória das interfaces de `application/interfaces` — usados pelos
testes unitários de caso de uso (nunca tocam banco de dados/Meilisearch reais)."""

from __future__ import annotations

import uuid

from src.application.interfaces.search_interface import ProductSearchDocument
from src.domain.entities.addon import AddonGroup
from src.domain.entities.category import Category
from src.domain.entities.product import Product


class FakeCategoryStore:
    def __init__(self, categories: list[Category] | None = None) -> None:
        self._categories: dict[uuid.UUID, Category] = {c.id: c for c in (categories or [])}

    async def get_by_id(self, category_id: uuid.UUID) -> Category | None:
        return self._categories.get(category_id)

    async def list_all(self) -> list[Category]:
        return list(self._categories.values())

    async def add(self, category: Category) -> Category:
        self._categories[category.id] = category
        return category


class FakeProductStore:
    def __init__(self, products: list[Product] | None = None) -> None:
        self._products: dict[uuid.UUID, Product] = {p.id: p for p in (products or [])}

    async def get_by_id(self, product_id: uuid.UUID) -> Product | None:
        return self._products.get(product_id)

    async def list_by_category(self, category_id: uuid.UUID) -> list[Product]:
        return [p for p in self._products.values() if p.category_id == category_id]

    async def list_all(self) -> list[Product]:
        return list(self._products.values())

    async def add(self, product: Product) -> Product:
        self._products[product.id] = product
        return product

    async def save(self, product: Product) -> Product:
        self._products[product.id] = product
        return product


class FakeAddonGroupStore:
    def __init__(self, groups: list[AddonGroup] | None = None) -> None:
        self._groups: dict[uuid.UUID, AddonGroup] = {g.id: g for g in (groups or [])}

    async def list_by_product(self, product_id: uuid.UUID) -> list[AddonGroup]:
        return [g for g in self._groups.values() if g.product_id == product_id]

    async def add(self, addon_group: AddonGroup) -> AddonGroup:
        self._groups[addon_group.id] = addon_group
        return addon_group


class FakeSearchIndex:
    """Índice de busca em memória — substitui o Meilisearch nos testes."""

    def __init__(self) -> None:
        self._documents: dict[str, ProductSearchDocument] = {}

    async def index_product(self, document: ProductSearchDocument) -> None:
        self._documents[document["id"]] = document

    async def remove_product(self, product_id: uuid.UUID) -> None:
        self._documents.pop(str(product_id), None)

    async def search(
        self, *, tenant_id: uuid.UUID, query: str, limit: int = 20
    ) -> list[ProductSearchDocument]:
        lowered_query = query.lower()
        matches = [
            doc
            for doc in self._documents.values()
            if doc["tenant_id"] == str(tenant_id) and lowered_query in doc["name"].lower()
        ]
        return matches[:limit]
