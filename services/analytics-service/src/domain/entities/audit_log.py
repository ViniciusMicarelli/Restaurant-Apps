"""Entidade `AuditLog` — registro imutável de auditoria técnica/operacional
(docs/modules/module_breakdown.md §12).

Consome eventos de domínio de TODOS os microsserviços via `restaurant_events`
(binding `#` no exchange `restaurant.domain_events`), sem exigir que cada
serviço conheça o `analytics-service` — apenas publica seus eventos normais
da Saga por coreografia (ADR-001) e este serviço os audita passivamente.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True)
class AuditLog:
    """Entrada imutável de auditoria — um evento de domínio já ocorrido em qualquer serviço."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    event_id: uuid.UUID
    event_type: str
    payload: dict[str, Any] = field(default_factory=dict)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if not self.event_type.strip():
            raise ValueError("O tipo do evento auditado não pode ser vazio.")
