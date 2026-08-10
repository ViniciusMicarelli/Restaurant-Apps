"""Caso de uso: movimentação manual de estoque (entrada, perda, devolução)."""

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

_POSITIVE_TYPES = (StockMovementType.ENTRY, StockMovementType.RETURN)


@dataclass
class RegisterStockMovementUseCase:
    inventory_item_repository: InventoryItemRepositoryInterface
    stock_movement_repository: StockMovementRepositoryInterface

    async def execute(
        self,
        *,
        inventory_item_id: uuid.UUID,
        movement_type: StockMovementType,
        quantity: float,
        reason: str | None,
    ) -> StockMovementResponse:
        item = await self.inventory_item_repository.get_by_id(inventory_item_id)
        if item is None:
            raise ResourceNotFoundException("InventoryItem", str(inventory_item_id))

        if movement_type in _POSITIVE_TYPES:
            item.increase(quantity)
            delta = quantity
        else:
            item.decrease(quantity)
            delta = -quantity

        await self.inventory_item_repository.save(item)

        movement = await self.stock_movement_repository.add(
            StockMovement(
                id=generate_uuid7(),
                tenant_id=item.tenant_id,
                inventory_item_id=item.id,
                movement_type=movement_type,
                quantity_delta=delta,
                reason=reason,
            )
        )
        return to_stock_movement_response(movement)
