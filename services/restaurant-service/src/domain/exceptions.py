"""Exceções de domínio específicas do serviço de Restaurantes."""

from __future__ import annotations

from restaurant_core.exceptions import BaseDomainException


class DuplicateSlugError(BaseDomainException):
    """Disparada ao tentar registrar um restaurante com um slug de URL já em uso."""

    def __init__(self, slug: str) -> None:
        super().__init__(
            message=f"O identificador de URL '{slug}' já está em uso por outro restaurante.",
            code="DUPLICATE_SLUG",
            status_code=409,
            details={"slug": slug},
        )


class PublicApiRateLimitExceededError(BaseDomainException):
    """Disparada quando uma rota pública (bootstrap de tenant, consulta por
    slug/ID) excede o teto de requisições da janela (docs/SECURITY.md §2.7).
    Sem tenant resolvível nessas rotas — a chave cai pro IP do cliente."""

    def __init__(self, retry_after_seconds: int) -> None:
        super().__init__(
            message="Muitas requisições. Tente novamente em instantes.",
            code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details={"retry_after_seconds": retry_after_seconds},
        )
