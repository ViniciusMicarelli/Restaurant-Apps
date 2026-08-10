"""Entidade de Domínio: Comanda (sessão de consumo aberta em uma mesa)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class CommandStatus(StrEnum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


@dataclass
class Command:
    """Comanda aberta por um garçom em uma mesa, associando um cliente à sessão de consumo."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    table_id: uuid.UUID
    customer_name: str
    waiter_id: uuid.UUID
    customer_cpf: str | None = None
    status: CommandStatus = CommandStatus.OPEN
    opened_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    closed_at: datetime | None = None
    service_fee_charged: bool = False

    def close(self) -> None:
        """Fecha a comanda, registrando o horário de encerramento."""
        if self.status == CommandStatus.CLOSED:
            raise ValueError("Esta comanda já está fechada.")
        self.status = CommandStatus.CLOSED
        self.closed_at = datetime.now(UTC)

    def set_service_fee(self, charged: bool) -> None:
        """Marca se a taxa de serviço foi cobrada nesta comanda (responsabilidade do garçom,
        pode ser alternada a qualquer momento antes do fechamento — docs/modules/module_breakdown.md §8)."""
        self.service_fee_charged = charged
