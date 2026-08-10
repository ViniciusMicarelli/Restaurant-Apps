"""Implementação concreta de `RecipeRepositoryInterface` sobre SQLAlchemy 2.0 Async."""

from __future__ import annotations

import uuid

from restaurant_database import SQLAlchemyRepository
from sqlalchemy import select
from src.domain.entities.recipe import Recipe, RecipeItem
from src.infrastructure.models.recipe_model import RecipeModel


def _to_entity(model: RecipeModel) -> Recipe:
    return Recipe(
        id=model.id,
        tenant_id=model.tenant_id,
        product_id=model.product_id,
        items=[
            RecipeItem(
                inventory_item_id=uuid.UUID(i["inventory_item_id"]),
                quantity_required=i["quantity_required"],
            )
            for i in model.items
        ],
    )


def _items_to_json(recipe: Recipe) -> list[dict[str, object]]:
    return [
        {"inventory_item_id": str(i.inventory_item_id), "quantity_required": i.quantity_required}
        for i in recipe.items
    ]


class SQLAlchemyRecipeRepository(SQLAlchemyRepository[RecipeModel]):
    model = RecipeModel

    async def get_by_product_id(self, product_id: uuid.UUID) -> Recipe | None:
        stmt = select(self.model).where(
            self.model.product_id == product_id,
            self.model.tenant_id == self._tenant_id,
            self.model.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def add(self, recipe: Recipe) -> Recipe:
        model = RecipeModel(
            id=recipe.id,
            tenant_id=recipe.tenant_id,
            product_id=recipe.product_id,
            items=_items_to_json(recipe),
        )
        created = await super().add_model(model)
        return _to_entity(created)

    async def save(self, recipe: Recipe) -> Recipe:
        model = await self._session.get(RecipeModel, recipe.id)
        if model is None:
            msg = f"Ficha técnica '{recipe.id}' não encontrada para atualização."
            raise LookupError(msg)
        model.items = _items_to_json(recipe)
        saved = await super().save_model(model)
        return _to_entity(saved)
