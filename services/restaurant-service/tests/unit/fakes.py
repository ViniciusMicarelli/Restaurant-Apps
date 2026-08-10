"""Fake em memória de `RestaurantRepositoryInterface` — usado pelos testes unitários."""

from __future__ import annotations

import uuid

from src.domain.entities.restaurant import Restaurant


class FakeRestaurantStore:
    def __init__(self, restaurants: list[Restaurant] | None = None) -> None:
        self._restaurants: dict[uuid.UUID, Restaurant] = {r.id: r for r in (restaurants or [])}

    async def get_by_id(self, restaurant_id: uuid.UUID) -> Restaurant | None:
        return self._restaurants.get(restaurant_id)

    async def get_by_slug(self, slug: str) -> Restaurant | None:
        return next((r for r in self._restaurants.values() if r.slug == slug), None)

    async def slug_exists(self, slug: str) -> bool:
        return await self.get_by_slug(slug) is not None

    async def add(self, restaurant: Restaurant) -> Restaurant:
        self._restaurants[restaurant.id] = restaurant
        return restaurant

    async def save(self, restaurant: Restaurant) -> Restaurant:
        self._restaurants[restaurant.id] = restaurant
        return restaurant
