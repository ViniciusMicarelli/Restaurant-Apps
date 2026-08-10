"""Entidade `StockMovement` — registro imutável de movimentação de estoque (auditoria)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class StockMovementType(StrEnum):
    """Motivo/origem de uma movimentação de estoque."""

    ENTRY = "ENTRY"  # Entrada manual (compra/recebimento de fornecedor)
    LOSS = "LOSS"  # Perda manual (quebra, validade vencida, etc.)
    RETURN = "RETURN"  # Devolução ao estoque (insumo não utilizado)
    COUNT_ADJUSTMENT = "COUNT_ADJUSTMENT"  # Ajuste por contagem de inventário
    SALE_DEDUCTION = "SALE_DEDUCTION"  # Baixa automática por venda (Saga `order.created`)


@dataclass(frozen=True)
class StockMovement:
    """Entrada imutável de auditoria de uma movimentação de estoque (append-only)."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    inventory_item_id: uuid.UUID
    movement_type: StockMovementType
    quantity_delta: float
    reason: str | None = None
    order_id: uuid.UUID | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
