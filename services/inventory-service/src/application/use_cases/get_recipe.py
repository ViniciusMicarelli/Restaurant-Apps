"""Caso de uso: consulta da ficha técnica de um produto."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from restaurant_core.exceptions import ResourceNotFoundException
from src.application.dtos.inventory_dtos import RecipeResponse
from src.application.interfaces.repository_interface import RecipeRepositoryInterface
from src.application.use_cases._shared import to_recipe_response


@dataclass
class GetRecipeUseCase:
    recipe_repository: RecipeRepositoryInterface

    async def execute(self, *, product_id: uuid.UUID) -> RecipeResponse:
        recipe = await self.recipe_repository.get_by_product_id(product_id)
        if recipe is None:
            raise ResourceNotFoundException("Recipe", str(product_id))
        return to_recipe_response(recipe)
