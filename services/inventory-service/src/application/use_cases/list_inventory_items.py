"""Caso de uso: listagem dos insumos em estoque, opcionalmente só os abaixo do mínimo."""

from __future__ import annotations

from dataclasses import dataclass

from src.application.dtos.inventory_dtos import InventoryItemResponse
from src.application.interfaces.repository_interface import InventoryItemRepositoryInterface
from src.application.use_cases._shared import to_inventory_item_response


@dataclass
class ListInventoryItemsUseCase:
    inventory_item_repository: InventoryItemRepositoryInterface

    async def execute(self, *, only_below_minimum: bool = False) -> list[InventoryItemResponse]:
        items = await self.inventory_item_repository.list_all()
        if only_below_minimum:
            items = [i for i in items if i.is_below_minimum]
        return [to_inventory_item_response(i) for i in items]
