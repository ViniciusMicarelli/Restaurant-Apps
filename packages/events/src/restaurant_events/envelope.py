"""Envelope padrão de Eventos de Domínio distribuídos entre microsserviços.

Todo evento publicado na Saga por coreografia (`OrderCreatedEvent`,
`StockDeductedEvent`, `PaymentFailedEvent`, etc.) é serializado dentro deste
envelope, garantindo rastreabilidade (`event_id`, `occurred_at`) e escopo de
tenant obrigatório em qualquer comunicação assíncrona entre serviços.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field
from restaurant_core.ids import generate_uuid7


class DomainEvent(BaseModel):
    """Envelope serializável de um evento de domínio publicado no barramento."""

    event_id: uuid.UUID = Field(default_factory=generate_uuid7)
    event_type: str = Field(
        ..., description="Nome do evento, ex: 'order.created', 'payment.failed'"
    )
    tenant_id: uuid.UUID
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    payload: dict[str, Any] = Field(default_factory=dict)
