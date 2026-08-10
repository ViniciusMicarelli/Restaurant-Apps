"""Caso de uso: contagem de estoque (inventário físico) — ajusta para o valor contado."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from restaurant_core.exceptions import ResourceNotFoundException
from restaurant_core.ids import generate_uuid7
from src.application.dtos.inventory_dtos import StockMovementResponse
from src.application.interfaces.repository_interface import (
    InventoryItemRepositoryInterface,
    StockMovementRepositoryInterface,
)
from src.application.use_cases._shared import to_stock_movement_response
from src.domain.entities.stock_movement import StockMovement, StockMovementType


@dataclass
class AdjustStockCountUseCase:
    inventory_item_repository: InventoryItemRepositoryInterface
    stock_movement_repository: StockMovementRepositoryInterface

    async def execute(
        self, *, inventory_item_id: uuid.UUID, counted_quantity: float, reason: str | None
    ) -> StockMovementResponse:
        item = await self.inventory_item_repository.get_by_id(inventory_item_id)
        if item is None:
            raise ResourceNotFoundException("InventoryItem", str(inventory_item_id))

        delta = item.adjust_to_counted_quantity(counted_quantity)
        await self.inventory_item_repository.save(item)

        movement = await self.stock_movement_repository.add(
            StockMovement(
                id=generate_uuid7(),
                tenant_id=item.tenant_id,
                inventory_item_id=item.id,
                movement_type=StockMovementType.COUNT_ADJUSTMENT,
                quantity_delta=delta,
                reason=reason,
            )
        )
        return to_stock_movement_response(movement)
