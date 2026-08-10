"""Exceções de domínio específicas do serviço de Estoque."""

from __future__ import annotations

from restaurant_core.exceptions import BaseDomainException


class InsufficientStockException(BaseDomainException):
    """Disparada ao tentar reduzir manualmente o estoque abaixo de zero.

    Não se aplica à baixa automática por venda (Saga por coreografia), que
    tolera estoque negativo por já refletir uma venda consumada em outro
    serviço (docs/ai/patterns.md — consistência eventual).
    """

    def __init__(self, item_name: str, current_quantity: float, requested_quantity: float) -> None:
        super().__init__(
            message=(
                f"Estoque insuficiente para '{item_name}': disponível {current_quantity}, "
                f"solicitado {requested_quantity}."
            ),
            code="INSUFFICIENT_STOCK",
            status_code=409,
            details={
                "item_name": item_name,
                "current_quantity": current_quantity,
                "requested_quantity": requested_quantity,
            },
        )
