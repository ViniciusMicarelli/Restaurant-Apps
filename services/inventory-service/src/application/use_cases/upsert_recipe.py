"""Caso de uso: criação/atualização da ficha técnica de um produto (US-02.4)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from restaurant_core.ids import generate_uuid7
from src.application.dtos.inventory_dtos import RecipeItemRequest, RecipeResponse
from src.application.interfaces.repository_interface import RecipeRepositoryInterface
from src.application.use_cases._shared import to_recipe_response
from src.domain.entities.recipe import Recipe, RecipeItem


@dataclass
class UpsertRecipeUseCase:
    recipe_repository: RecipeRepositoryInterface

    async def execute(
        self, *, tenant_id: uuid.UUID, product_id: uuid.UUID, items: list[RecipeItemRequest]
    ) -> RecipeResponse:
        domain_items = [
            RecipeItem(inventory_item_id=i.inventory_item_id, quantity_required=i.quantity_required)
            for i in items
        ]

        existing = await self.recipe_repository.get_by_product_id(product_id)
        if existing is None:
            recipe = Recipe(
                id=generate_uuid7(), tenant_id=tenant_id, product_id=product_id, items=domain_items
            )
            created = await self.recipe_repository.add(recipe)
            return to_recipe_response(created)

        existing.replace_items(domain_items)
        saved = await self.recipe_repository.save(existing)
        return to_recipe_response(saved)
