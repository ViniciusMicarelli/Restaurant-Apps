"""Módulo de Exceções Base do Sistema (RFC 7807 Problem Details).

Contém a hierarquia de exceções de domínio e aplicação para tratamento
padronizado e amigável ao usuário (Heurística de Usabilidade #9).
"""

from typing import Any


class BaseDomainException(Exception):
    """Exceção base para todas as violações de regras de negócio de domínio.

    Attributes:
        message (str): Mensagem descritiva do erro em português.
        code (str): Código único legível por máquinas (ex: 'INSUFFICIENT_STOCK').
        status_code (int): Código HTTP correspondente (default: 400).
        details (dict[str, Any] | None): Detalhes adicionais do erro.
    """

    def __init__(
        self,
        message: str,
        code: str = "DOMAIN_ERROR",
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class ResourceNotFoundException(BaseDomainException):
    """Disparada quando um recurso solicitado não existe ou não pertence ao tenant."""

    def __init__(self, resource_name: str, resource_id: str) -> None:
        super().__init__(
            message=f"O recurso '{resource_name}' com identificador '{resource_id}' não foi encontrado.",
            code="RESOURCE_NOT_FOUND",
            status_code=404,
            details={"resource_name": resource_name, "resource_id": resource_id},
        )


class UnauthorizedException(BaseDomainException):
    """Disparada em falhas de autenticação, credenciais inválidas ou token expirado."""

    def __init__(self, message: str = "Credenciais inválidas ou token expirado.") -> None:
        super().__init__(
            message=message,
            code="UNAUTHORIZED",
            status_code=401,
        )


class ForbiddenException(BaseDomainException):
    """Disparada quando o usuário autenticado não possui permissão RBAC/ABAC suficiente."""

    def __init__(self, message: str = "Você não possui permissão para executar esta ação.") -> None:
        super().__init__(
            message=message,
            code="FORBIDDEN",
            status_code=403,
        )


class OptimisticLockException(BaseDomainException):
    """Disparada em conflitos de concorrência quando outro usuário alterou o registro simultaneamente."""

    def __init__(self, resource_name: str) -> None:
        super().__init__(
            message=f"O registro '{resource_name}' foi alterado por outro operador. Atualize a tela e tente novamente.",
            code="CONCURRENCY_CONFLICT",
            status_code=409,
        )


class TenantIsolationException(BaseDomainException):
    """Disparada em tentativas de violação de escopo de tenant entre restaurantes."""

    def __init__(self) -> None:
        super().__init__(
            message="Tentativa não autorizada de acessar dados de outro restaurante.",
            code="TENANT_ISOLATION_VIOLATION",
            status_code=403,
        )
