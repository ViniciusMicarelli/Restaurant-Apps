"""Enumeração de meios de pagamento suportados (docs/modules/module_breakdown.md §8)."""

from __future__ import annotations

from enum import StrEnum


class PaymentMethod(StrEnum):
    """Meios de pagamento aceitos no fechamento de uma comanda."""

    CREDIT_CARD = "CREDIT_CARD"
    DEBIT_CARD = "DEBIT_CARD"
    PIX = "PIX"
    CASH = "CASH"
    VOUCHER = "VOUCHER"
