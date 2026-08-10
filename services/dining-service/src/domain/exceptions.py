"""Exceções de domínio específicas do serviço de Salão/Mesas/Comandas."""

from __future__ import annotations

from restaurant_core.exceptions import BaseDomainException


class TableNotAvailableError(BaseDomainException):
    """Disparada ao tentar abrir uma comanda em uma mesa que não está disponível."""

    def __init__(self, table_number: int) -> None:
        super().__init__(
            message=f"A mesa {table_number} não está disponível para abertura de comanda.",
            code="TABLE_NOT_AVAILABLE",
            status_code=409,
            details={"table_number": table_number},
        )


class DuplicateTableNumberError(BaseDomainException):
    """Disparada ao tentar cadastrar uma mesa com número já em uso no tenant."""

    def __init__(self, number: int) -> None:
        super().__init__(
            message=f"Já existe uma mesa com o número {number} cadastrada.",
            code="DUPLICATE_TABLE_NUMBER",
            status_code=409,
            details={"number": number},
        )


class TableNotAwaitingCleaningError(BaseDomainException):
    """Disparada ao tentar liberar (marcar como limpa) uma mesa que não está
    em `WAITING_CLEANING` — só faz sentido liberar uma mesa que acabou de
    ter a comanda encerrada."""

    def __init__(self, table_number: int) -> None:
        super().__init__(
            message=f"A mesa {table_number} não está aguardando limpeza.",
            code="TABLE_NOT_AWAITING_CLEANING",
            status_code=409,
            details={"table_number": table_number},
        )


class PublicApiRateLimitExceededError(BaseDomainException):
    """Disparada quando uma rota pública (autoatendimento do cliente via QR
    Code) excede o teto de requisições da janela (docs/SECURITY.md §2.7)."""

    def __init__(self, retry_after_seconds: int) -> None:
        super().__init__(
            message="Muitas requisições. Tente novamente em instantes.",
            code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details={"retry_after_seconds": retry_after_seconds},
        )


class InvalidOrExpiredQrSecretError(BaseDomainException):
    """Disparada quando o cardápio digital é aberto com uma secret de mesa
    ausente, incorreta ou expirada — a QR Code rotativa é obrigatória."""

    def __init__(self, table_number: int) -> None:
        super().__init__(
            message=(
                f"QR Code da mesa {table_number} inválido ou expirado. "
                "Peça a um garçom para gerar um novo."
            ),
            code="INVALID_OR_EXPIRED_QR_SECRET",
            status_code=401,
            details={"table_number": table_number},
        )
