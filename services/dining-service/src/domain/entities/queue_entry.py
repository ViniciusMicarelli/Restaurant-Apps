"""Entidade de Domínio: Entrada na Fila de Espera Virtual."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class QueueStatus(StrEnum):
    WAITING = "WAITING"
    NOTIFIED = "NOTIFIED"
    SEATED = "SEATED"
    CANCELLED = "CANCELLED"


@dataclass
class QueueEntry:
    """Cliente aguardando uma mesa disponível na fila de espera virtual."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    customer_name: str
    phone: str
    party_size: int
    status: QueueStatus = QueueStatus.WAITING
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if self.party_size < 1:
            raise ValueError("party_size deve ser pelo menos 1.")
