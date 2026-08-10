"""Entidade `KDSLog` — registro imutável de auditoria de transições de status no KDS."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from src.domain.entities.kds_item import KDSItemStatus


@dataclass(frozen=True)
class KDSLog:
    """Entrada imutável de auditoria: uma transição de status de um `KDSItem`.

    Nunca é atualizada ou removida após criada — apenas inserida (append-only).
    """

    id: uuid.UUID
    tenant_id: uuid.UUID
    kds_item_id: uuid.UUID
    from_status: KDSItemStatus
    to_status: KDSItemStatus
    changed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
