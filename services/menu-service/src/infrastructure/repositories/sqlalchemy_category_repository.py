"""Implementação concreta de `CategoryRepositoryInterface` sobre SQLAlchemy 2.0 Async."""

from __future__ import annotations

import uuid

from restaurant_database import SQLAlchemyRepository
from src.domain.entities.category import Category
from src.infrastructure.models.category_model import CategoryModel


def _to_entity(model: CategoryModel) -> Category:
    return Category(
        id=model.id,
        tenant_id=model.tenant_id,
        name=model.name,
        display_order=model.display_order,
        is_active=model.is_active,
    )


class SQLAlchemyCategoryRepository(SQLAlchemyRepository[CategoryModel]):
    model = CategoryModel

    async def get_by_id(self, category_id: uuid.UUID) -> Category | None:
        model = await super().get_model_by_id(category_id)
        return _to_entity(model) if model is not None else None

    async def list_all(self, *, limit: int = 1000, offset: int = 0) -> list[Category]:
        models = await super().list_models(limit=limit, offset=offset)
        return [_to_entity(m) for m in models]

    async def add(self, category: Category) -> Category:
        model = CategoryModel(
            id=category.id,
            tenant_id=category.tenant_id,
            name=category.name,
            display_order=category.display_order,
            is_active=category.is_active,
        )
        created = await super().add_model(model)
        return _to_entity(created)
