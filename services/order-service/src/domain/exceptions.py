"""Exceções de domínio específicas do serviço de Pedidos."""

from __future__ import annotations

from restaurant_core.exceptions import BaseDomainException


class InvalidOrderTransitionError(BaseDomainException):
    """Disparada ao tentar aplicar uma transição de status inválida."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, code="INVALID_ORDER_TRANSITION", status_code=409)


class EmptyOrderError(BaseDomainException):
    """Disparada ao tentar criar um pedido sem nenhum item."""

    def __init__(self) -> None:
        super().__init__(
            message="Um pedido deve conter ao menos um item.", code="EMPTY_ORDER", status_code=422
        )
