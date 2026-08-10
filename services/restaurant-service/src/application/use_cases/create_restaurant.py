"""Caso de uso: cadastro público de um novo restaurante (bootstrap de tenant)."""

from __future__ import annotations

from dataclasses import dataclass

from restaurant_core.ids import generate_uuid7
from src.application.dtos.restaurant_dtos import RestaurantResponse
from src.application.interfaces.repository_interface import RestaurantRepositoryInterface
from src.application.use_cases._shared import to_restaurant_response
from src.domain.entities.restaurant import Restaurant, RestaurantBranding
from src.domain.exceptions import DuplicateSlugError


@dataclass
class CreateRestaurantUseCase:
    """Cria um `Restaurant` — seu `id` se torna o `tenant_id` usado no resto da plataforma."""

    restaurant_repository: RestaurantRepositoryInterface

    async def execute(  # noqa: PLR0913 - parâmetros nomeados (keyword-only) mapeando 1:1 com o DTO de entrada
        self,
        *,
        slug: str,
        trade_name: str,
        legal_name: str,
        cnpj: str,
        phone: str,
        currency: str = "BRL",
        service_fee_percent: float = 10.0,
    ) -> RestaurantResponse:
        if await self.restaurant_repository.slug_exists(slug):
            raise DuplicateSlugError(slug)

        restaurant = Restaurant(
            id=generate_uuid7(),
            slug=slug,
            trade_name=trade_name,
            legal_name=legal_name,
            cnpj=cnpj,
            phone=phone,
            currency=currency,
            service_fee_percent=service_fee_percent,
            branding=RestaurantBranding(),
        )
        created = await self.restaurant_repository.add(restaurant)
        return to_restaurant_response(created)
