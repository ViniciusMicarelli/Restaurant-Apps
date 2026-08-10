"""Exceções de domínio específicas do serviço de Autenticação.

Casos genéricos (não encontrado, não autorizado, conflito de concorrência,
violação de tenant) já são cobertos por `restaurant_core.exceptions` — aqui
só entram exceções cujo significado é específico deste domínio.
"""

from __future__ import annotations

from restaurant_core.exceptions import BaseDomainException


class DuplicateEmailError(BaseDomainException):
    """Disparada ao tentar registrar um usuário com e-mail já cadastrado no tenant."""

    def __init__(self, email: str) -> None:
        super().__init__(
            message=f"O e-mail '{email}' já está cadastrado para este restaurante.",
            code="DUPLICATE_EMAIL",
            status_code=409,
            details={"email": email},
        )


class InvalidCredentialsError(BaseDomainException):
    """Disparada em falha de autenticação por e-mail/senha ou PIN."""

    def __init__(self, message: str = "Credenciais inválidas.") -> None:
        super().__init__(message=message, code="INVALID_CREDENTIALS", status_code=401)


class PinLoginNotAllowedError(BaseDomainException):
    """Disparada quando um usuário sem elegibilidade tenta autenticar via PIN."""

    def __init__(self) -> None:
        super().__init__(
            message="Este usuário não possui login por PIN habilitado.",
            code="PIN_LOGIN_NOT_ALLOWED",
            status_code=403,
        )


class TokenRevokedError(BaseDomainException):
    """Disparada ao tentar usar um token cujo `jti` foi revogado (logout/rotação)."""

    def __init__(self) -> None:
        super().__init__(
            message="Este token foi revogado. Faça login novamente.",
            code="TOKEN_REVOKED",
            status_code=401,
        )


class RateLimitExceededError(BaseDomainException):
    """Disparada quando um IP excede o limite de tentativas de login numa
    janela de tempo (docs/SECURITY.md §2.7 — força bruta)."""

    def __init__(self, retry_after_seconds: int) -> None:
        super().__init__(
            message="Muitas tentativas de login. Tente novamente em instantes.",
            code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details={"retry_after_seconds": retry_after_seconds},
        )
