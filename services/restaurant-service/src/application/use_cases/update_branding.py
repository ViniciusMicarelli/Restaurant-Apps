"""Caso de uso: atualização do tema/branding White-Label de um restaurante."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from restaurant_core.exceptions import ResourceNotFoundException, TenantIsolationException
from src.application.dtos.restaurant_dtos import RestaurantResponse, UpdateBrandingRequest
from src.application.interfaces.repository_interface import RestaurantRepositoryInterface
from src.application.use_cases._shared import to_restaurant_response
from src.domain.entities.restaurant import RestaurantBranding


@dataclass
class UpdateBrandingUseCase:
    restaurant_repository: RestaurantRepositoryInterface

    async def execute(
        self,
        *,
        restaurant_id: uuid.UUID,
        acting_tenant_id: uuid.UUID,
        payload: UpdateBrandingRequest,
    ) -> RestaurantResponse:
        if restaurant_id != acting_tenant_id:
            raise TenantIsolationException()

        restaurant = await self.restaurant_repository.get_by_id(restaurant_id)
        if restaurant is None:
            raise ResourceNotFoundException("Restaurant", str(restaurant_id))

        restaurant.branding = RestaurantBranding(
            primary_color=payload.primary_color,
            secondary_color=payload.secondary_color,
            accent_color=payload.accent_color,
            background_color=payload.background_color,
            surface_color=payload.surface_color,
            theme_mode=payload.theme_mode,
            logo_url=payload.logo_url,
            favicon_url=payload.favicon_url,
            banner_url=payload.banner_url,
            font_family=payload.font_family,
            border_radius=payload.border_radius,
        )

        updated = await self.restaurant_repository.save(restaurant)
        return to_restaurant_response(updated)
