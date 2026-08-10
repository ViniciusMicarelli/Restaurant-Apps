"""Caso de uso: cadastro de Grupos de Adicionais de um produto."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from restaurant_core.exceptions import ResourceNotFoundException
from restaurant_core.ids import generate_uuid7
from src.application.dtos.menu_dtos import (
    AddonGroupResponse,
    AddonOptionRequest,
    AddonOptionResponse,
)
from src.application.interfaces.repository_interface import (
    AddonGroupRepositoryInterface,
    ProductRepositoryInterface,
)
from src.domain.entities.addon import AddonGroup, AddonOption


def _to_response(group: AddonGroup) -> AddonGroupResponse:
    return AddonGroupResponse(
        id=group.id,
        tenant_id=group.tenant_id,
        product_id=group.product_id,
        name=group.name,
        min_selections=group.min_selections,
        max_selections=group.max_selections,
        options=[
            AddonOptionResponse(name=o.name, price_delta=o.price_delta) for o in group.options
        ],
    )


@dataclass
class CreateAddonGroupUseCase:
    addon_group_repository: AddonGroupRepositoryInterface
    product_repository: ProductRepositoryInterface

    async def execute(  # noqa: PLR0913 - parâmetros nomeados (keyword-only) mapeando 1:1 com o DTO de entrada
        self,
        *,
        tenant_id: uuid.UUID,
        product_id: uuid.UUID,
        name: str,
        min_selections: int,
        max_selections: int,
        options: list[AddonOptionRequest],
    ) -> AddonGroupResponse:
        if await self.product_repository.get_by_id(product_id) is None:
            raise ResourceNotFoundException("Product", str(product_id))

        addon_group = AddonGroup(
            id=generate_uuid7(),
            tenant_id=tenant_id,
            product_id=product_id,
            name=name,
            min_selections=min_selections,
            max_selections=max_selections,
            options=[AddonOption(name=o.name, price_delta=o.price_delta) for o in options],
        )
        created = await self.addon_group_repository.add(addon_group)
        return _to_response(created)


@dataclass
class ListAddonGroupsUseCase:
    addon_group_repository: AddonGroupRepositoryInterface

    async def execute(self, *, product_id: uuid.UUID) -> list[AddonGroupResponse]:
        groups = await self.addon_group_repository.list_by_product(product_id)
        return [_to_response(g) for g in groups]
