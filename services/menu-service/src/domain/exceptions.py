"""Exceções de domínio específicas do serviço de Cardápio."""

from __future__ import annotations

from restaurant_core.exceptions import BaseDomainException


class PublicApiRateLimitExceededError(BaseDomainException):
    """Disparada quando uma rota pública (cardápio digital do autoatendimento)
    excede o teto de requisições da janela (docs/SECURITY.md §2.7)."""

    def __init__(self, retry_after_seconds: int) -> None:
        super().__init__(
            message="Muitas requisições. Tente novamente em instantes.",
            code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details={"retry_after_seconds": retry_after_seconds},
        )
