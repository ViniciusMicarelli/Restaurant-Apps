"""Caso de uso: transição de status de um item do KDS (US-04.3).

Toda transição gera uma entrada imutável em `KDSLog` (auditoria) e uma
notificação instantânea via WebSocket para os monitores e apps de garçons
conectados do mesmo tenant.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from restaurant_core.exceptions import ResourceNotFoundException
from restaurant_core.ids import generate_uuid7
from src.application.dtos.kds_dtos import KDSItemResponse
from src.application.interfaces.repository_interface import (
    KDSBroadcasterInterface,
    KDSItemRepositoryInterface,
    KDSLogRepositoryInterface,
)
from src.application.use_cases._shared import to_kds_item_response
from src.domain.entities.kds_item import KDSItemStatus
from src.domain.entities.kds_log import KDSLog
from src.domain.exceptions import InvalidKDSTransitionError


@dataclass
class UpdateKDSItemStatusUseCase:
    kds_item_repository: KDSItemRepositoryInterface
    kds_log_repository: KDSLogRepositoryInterface
    broadcaster: KDSBroadcasterInterface

    async def execute(
        self, *, kds_item_id: uuid.UUID, new_status: KDSItemStatus
    ) -> KDSItemResponse:
        item = await self.kds_item_repository.get_by_id(kds_item_id)
        if item is None:
            raise ResourceNotFoundException("KDSItem", str(kds_item_id))

        previous_status = item.status
        try:
            item.transition_to(new_status)
        except ValueError as exc:
            raise InvalidKDSTransitionError(str(exc)) from exc

        updated = await self.kds_item_repository.save(item)

        await self.kds_log_repository.add(
            KDSLog(
                id=generate_uuid7(),
                tenant_id=updated.tenant_id,
                kds_item_id=updated.id,
                from_status=previous_status,
                to_status=updated.status,
            )
        )

        response = to_kds_item_response(updated)
        await self.broadcaster.broadcast(
            updated.tenant_id,
            {
                "event": "KDS_ITEM_STATUS_CHANGED",
                "item": response.model_dump(mode="json"),
            },
        )
        return response
