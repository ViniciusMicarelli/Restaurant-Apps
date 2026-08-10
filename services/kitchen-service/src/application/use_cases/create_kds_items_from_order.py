"""Caso de uso: criação dos itens do KDS a partir do evento `order.created`.

Consumido de forma assíncrona e desacoplada via `restaurant_events` (Saga por
coreografia, ADR-001) — nenhuma chamada HTTP direta ao `order-service`.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from restaurant_core.ids import generate_uuid7
from src.application.dtos.kds_dtos import KDSItemResponse
from src.application.interfaces.repository_interface import (
    KDSBroadcasterInterface,
    KDSItemRepositoryInterface,
)
from src.application.use_cases._shared import to_kds_item_response
from src.domain.entities.kds_item import KDSItem, KDSStation


@dataclass
class CreateKDSItemsFromOrderUseCase:
    kds_item_repository: KDSItemRepositoryInterface
    broadcaster: KDSBroadcasterInterface

    async def execute(
        self,
        *,
        tenant_id: uuid.UUID,
        order_id: uuid.UUID,
        table_number: int | None,
        items: list[dict[str, Any]],
    ) -> list[KDSItemResponse]:
        created: list[KDSItemResponse] = []
        for raw_item in items:
            item = KDSItem(
                id=generate_uuid7(),
                tenant_id=tenant_id,
                order_id=order_id,
                product_id=uuid.UUID(str(raw_item["product_id"])),
                product_name=str(raw_item["product_name"]),
                quantity=int(raw_item["quantity"]),
                station=KDSStation.COZINHA_QUENTE,
                table_number=table_number,
            )
            saved = await self.kds_item_repository.add(item)
            response = to_kds_item_response(saved)
            created.append(response)

            await self.broadcaster.broadcast(
                tenant_id,
                {
                    "event": "KDS_ITEM_CREATED",
                    "item": response.model_dump(mode="json"),
                },
            )

        return created
