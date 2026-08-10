"""Exceções de domínio específicas do serviço de Delivery."""

from __future__ import annotations

from restaurant_core.exceptions import BaseDomainException


class InvalidDeliveryTransitionError(BaseDomainException):
    """Disparada ao tentar aplicar uma transição de status inválida a uma entrega."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, code="INVALID_DELIVERY_TRANSITION", status_code=409)
