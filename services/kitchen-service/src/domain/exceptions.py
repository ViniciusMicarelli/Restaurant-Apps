"""Exceções de domínio específicas do serviço de Cozinha/KDS."""

from __future__ import annotations

from restaurant_core.exceptions import BaseDomainException


class InvalidKDSTransitionError(BaseDomainException):
    """Disparada ao tentar aplicar uma transição de status inválida a um item do KDS."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, code="INVALID_KDS_TRANSITION", status_code=409)
