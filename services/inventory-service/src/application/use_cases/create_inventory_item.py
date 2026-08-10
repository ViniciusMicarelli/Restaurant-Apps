"""Caso de uso: cadastro de um novo insumo controlado em estoque."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from restaurant_core.ids import generate_uuid7
from src.application.dtos.inventory_dtos import InventoryItemResponse
from src.application.interfaces.repository_interface import InventoryItemRepositoryInterface
from src.application.use_cases._shared import to_inventory_item_response
from src.domain.entities.inventory_item import InventoryItem, InventoryUnit


@dataclass
class CreateInventoryItemUseCase:
    inventory_item_repository: InventoryItemRepositoryInterface

    async def execute(  # noqa: PLR0913 - parâmetros nomeados (keyword-only) mapeando 1:1 com o DTO de entrada
        self,
        *,
        tenant_id: uuid.UUID,
        name: str,
        unit: InventoryUnit,
        initial_quantity: float,
        minimum_quantity: float,
        supplier_id: uuid.UUID | None,
    ) -> InventoryItemResponse:
        item = InventoryItem(
            id=generate_uuid7(),
            tenant_id=tenant_id,
            name=name,
            unit=unit,
            current_quantity=initial_quantity,
            minimum_quantity=minimum_quantity,
            supplier_id=supplier_id,
        )
        created = await self.inventory_item_repository.add(item)
        return to_inventory_item_response(created)
