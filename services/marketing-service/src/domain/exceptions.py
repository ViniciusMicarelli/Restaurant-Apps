"""Exceções de domínio específicas do serviço de Marketing."""

from __future__ import annotations

from restaurant_core.exceptions import BaseDomainException


class InvalidCouponException(BaseDomainException):
    """Disparada ao tentar aplicar um cupom expirado, inativo ou com limite de usos esgotado."""

    def __init__(self, code: str) -> None:
        super().__init__(
            message=f"O cupom '{code}' é inválido, está expirado ou atingiu o limite de usos.",
            code="INVALID_COUPON",
            status_code=409,
        )


class DuplicateCouponCodeException(BaseDomainException):
    """Disparada ao tentar cadastrar um código de cupom já existente para o tenant."""

    def __init__(self, code: str) -> None:
        super().__init__(
            message=f"Já existe um cupom com o código '{code}' para este restaurante.",
            code="DUPLICATE_COUPON_CODE",
            status_code=409,
        )
