"""Casos de uso da Fila de Espera Virtual."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from restaurant_core.exceptions import ResourceNotFoundException
from restaurant_core.ids import generate_uuid7
from src.application.dtos.dining_dtos import QueueEntryResponse
from src.application.interfaces.repository_interface import QueueRepositoryInterface
from src.domain.entities.queue_entry import QueueEntry, QueueStatus


def _to_response(entry: QueueEntry, position: int) -> QueueEntryResponse:
    return QueueEntryResponse(
        id=entry.id,
        tenant_id=entry.tenant_id,
        customer_name=entry.customer_name,
        phone=entry.phone,
        party_size=entry.party_size,
        status=entry.status,
        position=position,
    )


@dataclass
class AddToQueueUseCase:
    queue_repository: QueueRepositoryInterface

    async def execute(
        self, *, tenant_id: uuid.UUID, customer_name: str, phone: str, party_size: int
    ) -> QueueEntryResponse:
        entry = QueueEntry(
            id=generate_uuid7(),
            tenant_id=tenant_id,
            customer_name=customer_name,
            phone=phone,
            party_size=party_size,
        )
        created = await self.queue_repository.add(entry)

        waiting = await self.queue_repository.list_waiting()
        position = next((i + 1 for i, e in enumerate(waiting) if e.id == created.id), len(waiting))
        return _to_response(created, position)


@dataclass
class ListQueueUseCase:
    queue_repository: QueueRepositoryInterface

    async def execute(self) -> list[QueueEntryResponse]:
        waiting = await self.queue_repository.list_waiting()
        return [_to_response(entry, position=i + 1) for i, entry in enumerate(waiting)]


@dataclass
class CallNextInQueueUseCase:
    """Marca a próxima entrada da fila como `NOTIFIED` (cliente chamado para ser sentado)."""

    queue_repository: QueueRepositoryInterface

    async def execute(self) -> QueueEntryResponse:
        waiting = await self.queue_repository.list_waiting()
        if not waiting:
            raise ResourceNotFoundException("QueueEntry", "next")

        next_entry = waiting[0]
        next_entry.status = QueueStatus.NOTIFIED
        updated = await self.queue_repository.save(next_entry)
        return _to_response(updated, position=1)
