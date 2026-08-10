"""Entidade `CashMovement` — registro imutável de movimentação de um caixa (auditoria)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class CashMovementType(StrEnum):
    """Tipo/origem de uma movimentação de caixa."""

    OPENING_FLOAT = "OPENING_FLOAT"  # Suprimento inicial de troco (abertura)
    SALE = "SALE"  # Recebimento de venda em dinheiro
    SANGRIA = "SANGRIA"  # Retirada de sangria para o cofre
    SUPPLY = "SUPPLY"  # Entrada manual de troco adicional


@dataclass(frozen=True)
class CashMovement:
    """Entrada imutável de auditoria de uma movimentação de caixa (append-only)."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    cash_register_id: uuid.UUID
    movement_type: CashMovementType
    amount_delta: float
    reason: str | None = None
    payment_id: uuid.UUID | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
