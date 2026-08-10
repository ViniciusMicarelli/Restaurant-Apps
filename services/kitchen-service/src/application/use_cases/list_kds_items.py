"""Caso de uso: listagem dos itens ativos na esteira do KDS, opcionalmente por estação."""

from __future__ import annotations

from dataclasses import dataclass

from src.application.dtos.kds_dtos import KDSItemResponse
from src.application.interfaces.repository_interface import KDSItemRepositoryInterface
from src.application.use_cases._shared import to_kds_item_response
from src.domain.entities.kds_item import KDSStation


@dataclass
class ListKDSItemsUseCase:
    kds_item_repository: KDSItemRepositoryInterface

    async def execute(self, *, station: KDSStation | None = None) -> list[KDSItemResponse]:
        items = await self.kds_item_repository.list_all(station=station)
        return [to_kds_item_response(item) for item in items]
