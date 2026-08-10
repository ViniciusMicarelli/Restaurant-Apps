"""Caso de uso: atualização dos dados operacionais de um restaurante pelo seu próprio Owner/Manager."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from restaurant_core.exceptions import ResourceNotFoundException, TenantIsolationException
from src.application.dtos.restaurant_dtos import RestaurantResponse
from src.application.interfaces.repository_interface import RestaurantRepositoryInterface
from src.application.use_cases._shared import to_restaurant_response


@dataclass
class UpdateRestaurantUseCase:
    """Atualiza campos operacionais — só o próprio tenant pode alterar seus dados.

    `acting_tenant_id` vem do JWT do usuário autenticado (nunca do path/body),
    e é comparado contra o `id` do restaurante-alvo antes de qualquer escrita.
    """

    restaurant_repository: RestaurantRepositoryInterface

    async def execute(  # noqa: PLR0913 - parâmetros nomeados (keyword-only) mapeando 1:1 com o DTO de entrada
        self,
        *,
        restaurant_id: uuid.UUID,
        acting_tenant_id: uuid.UUID,
        trade_name: str,
        phone: str,
        currency: str,
        service_fee_percent: float,
    ) -> RestaurantResponse:
        if restaurant_id != acting_tenant_id:
            raise TenantIsolationException()

        restaurant = await self.restaurant_repository.get_by_id(restaurant_id)
        if restaurant is None:
            raise ResourceNotFoundException("Restaurant", str(restaurant_id))

        restaurant.trade_name = trade_name
        restaurant.phone = phone
        restaurant.currency = currency
        restaurant.service_fee_percent = service_fee_percent

        updated = await self.restaurant_repository.save(restaurant)
        return to_restaurant_response(updated)
