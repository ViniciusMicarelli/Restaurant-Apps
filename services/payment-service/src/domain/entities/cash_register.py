"""Entidade `CashRegister` — caixa operacional do restaurante (docs/modules/module_breakdown.md §8)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum


class CashRegisterStatus(StrEnum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


@dataclass
class CashRegister:
    """Caixa operacional: controla o saldo físico em dinheiro desde a abertura
    (suprimento inicial) até o fechamento cego (US-05.1, US-05.3).

    Attributes:
        id: UUIDv7 do caixa.
        tenant_id: ID do restaurante proprietário.
        operator_id: ID do operador/caixa responsável.
        opening_amount: Troco inicial informado na abertura (suprimento).
        current_balance: Saldo físico em dinheiro acumulado (só movimentos `CASH`).
        status: `OPEN` ou `CLOSED`.
        opened_at: Data/hora de abertura.
        closed_at: Data/hora de fechamento (nula enquanto aberto).
        closing_counted_amount: Valor contado fisicamente no fechamento cego — o
            operador não vê `current_balance` antes de informar esse valor
            (US-05.3), evitando ajuste da contagem para "bater" o sistema.
        closing_divergence: `closing_counted_amount - current_balance` no
            momento do fechamento — positivo (sobra) ou negativo (falta).
    """

    id: uuid.UUID
    tenant_id: uuid.UUID
    operator_id: uuid.UUID
    opening_amount: float
    current_balance: float = 0.0
    status: CashRegisterStatus = CashRegisterStatus.OPEN
    opened_at: datetime | None = None
    closed_at: datetime | None = None
    closing_counted_amount: float | None = None
    closing_divergence: float | None = None

    def __post_init__(self) -> None:
        if self.opening_amount < 0:
            raise ValueError("O valor de abertura do caixa não pode ser negativo.")
        if self.opened_at is None:
            self.opened_at = datetime.now(UTC)

    def apply_cash_movement(self, amount_delta: float) -> None:
        """Aplica uma movimentação em dinheiro físico ao saldo (positiva ou negativa).

        Raises:
            ValueError: Se o caixa já estiver fechado, ou se a movimentação
                resultar em saldo negativo (sangria/venda maior que o disponível).
        """
        if self.status != CashRegisterStatus.OPEN:
            raise ValueError("Não é possível movimentar um caixa fechado.")

        resulting = round(self.current_balance + amount_delta, 2)
        if resulting < 0:
            raise ValueError("A movimentação resultaria em saldo negativo no caixa.")
        self.current_balance = resulting

    def close(self, counted_amount: float) -> None:
        """Realiza o fechamento cego do caixa (US-05.3): registra o valor
        contado fisicamente e calcula a divergência frente ao saldo do sistema.
        """
        if self.status != CashRegisterStatus.OPEN:
            raise ValueError("O caixa já está fechado.")
        if counted_amount < 0:
            raise ValueError("O valor contado no fechamento não pode ser negativo.")

        self.closing_counted_amount = round(counted_amount, 2)
        self.closing_divergence = round(counted_amount - self.current_balance, 2)
        self.status = CashRegisterStatus.CLOSED
        self.closed_at = datetime.now(UTC)
