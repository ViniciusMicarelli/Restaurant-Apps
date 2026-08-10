"""Casos de uso de Categorias do Cardápio."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from restaurant_core.ids import generate_uuid7
from src.application.dtos.menu_dtos import CategoryResponse
from src.application.interfaces.repository_interface import CategoryRepositoryInterface
from src.domain.entities.category import Category


def _to_response(category: Category) -> CategoryResponse:
    return CategoryResponse(
        id=category.id,
        tenant_id=category.tenant_id,
        name=category.name,
        display_order=category.display_order,
        is_active=category.is_active,
    )


@dataclass
class CreateCategoryUseCase:
    category_repository: CategoryRepositoryInterface

    async def execute(
        self, *, tenant_id: uuid.UUID, name: str, display_order: int = 0
    ) -> CategoryResponse:
        category = Category(
            id=generate_uuid7(), tenant_id=tenant_id, name=name, display_order=display_order
        )
        created = await self.category_repository.add(category)
        return _to_response(created)


@dataclass
class ListCategoriesUseCase:
    category_repository: CategoryRepositoryInterface

    async def execute(self) -> list[CategoryResponse]:
        categories = await self.category_repository.list_all()
        return [_to_response(c) for c in sorted(categories, key=lambda c: c.display_order)]
