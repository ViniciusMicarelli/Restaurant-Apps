"""Casos de uso: consulta de um restaurante por ID ou por slug público."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from restaurant_core.exceptions import ResourceNotFoundException
from src.application.dtos.restaurant_dtos import RestaurantResponse
from src.application.interfaces.repository_interface import RestaurantRepositoryInterface
from src.application.use_cases._shared import to_restaurant_response


@dataclass
class GetRestaurantByIdUseCase:
    restaurant_repository: RestaurantRepositoryInterface

    async def execute(self, *, restaurant_id: uuid.UUID) -> RestaurantResponse:
        restaurant = await self.restaurant_repository.get_by_id(restaurant_id)
        if restaurant is None:
            raise ResourceNotFoundException("Restaurant", str(restaurant_id))
        return to_restaurant_response(restaurant)


@dataclass
class GetRestaurantBySlugUseCase:
    restaurant_repository: RestaurantRepositoryInterface

    async def execute(self, *, slug: str) -> RestaurantResponse:
        restaurant = await self.restaurant_repository.get_by_slug(slug)
        if restaurant is None:
            raise ResourceNotFoundException("Restaurant", slug)
        return to_restaurant_response(restaurant)
