"""Caso de uso: baixa automática de insumos a partir do evento `order.created` (US-02.4).

Consumido de forma assíncrona e desacoplada via `restaurant_events` (Saga por
coreografia, ADR-001). Produtos sem ficha técnica cadastrada são ignorados
silenciosamente — nem todo produto vendido precisa controlar insumos (ex:
uma bebida industrializada revendida sem preparo).
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Any

from restaurant_core.ids import generate_uuid7
from src.application.interfaces.repository_interface import (
    InventoryItemRepositoryInterface,
    RecipeRepositoryInterface,
    StockMovementRepositoryInterface,
)
from src.domain.entities.stock_movement import StockMovement, StockMovementType

logger = logging.getLogger(__name__)


@dataclass
class DeductStockForOrderUseCase:
    inventory_item_repository: InventoryItemRepositoryInterface
    recipe_repository: RecipeRepositoryInterface
    stock_movement_repository: StockMovementRepositoryInterface

    async def execute(
        self, *, tenant_id: uuid.UUID, order_id: uuid.UUID, items: list[dict[str, Any]]
    ) -> None:
        for raw_item in items:
            product_id = uuid.UUID(str(raw_item["product_id"]))
            quantity_sold = int(raw_item["quantity"])

            recipe = await self.recipe_repository.get_by_product_id(product_id)
            if recipe is None:
                continue

            for recipe_item in recipe.items:
                inventory_item = await self.inventory_item_repository.get_by_id(
                    recipe_item.inventory_item_id
                )
                if inventory_item is None:
                    logger.warning(
                        "Insumo '%s' da ficha técnica do produto '%s' não encontrado.",
                        recipe_item.inventory_item_id,
                        product_id,
                    )
                    continue

                deducted = recipe_item.quantity_required * quantity_sold
                inventory_item.decrease(deducted, allow_negative=True)
                await self.inventory_item_repository.save(inventory_item)

                await self.stock_movement_repository.add(
                    StockMovement(
                        id=generate_uuid7(),
                        tenant_id=tenant_id,
                        inventory_item_id=inventory_item.id,
                        movement_type=StockMovementType.SALE_DEDUCTION,
                        quantity_delta=-deducted,
                        order_id=order_id,
                    )
                )
