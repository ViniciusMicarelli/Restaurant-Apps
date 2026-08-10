"""Exceções de domínio específicas do serviço de Pagamentos e Caixa."""

from __future__ import annotations

from restaurant_core.exceptions import BaseDomainException


class CashOperationException(BaseDomainException):
    """Disparada em operações inválidas sobre um caixa (fechado, saldo insuficiente, etc.)."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, code="CASH_OPERATION_ERROR", status_code=409)


class OperatorAlreadyHasOpenCashRegisterException(BaseDomainException):
    """Disparada ao tentar abrir um segundo caixa para o mesmo operador sem fechar o anterior."""

    def __init__(self, operator_id: str) -> None:
        super().__init__(
            message=f"O operador '{operator_id}' já possui um caixa aberto.",
            code="OPERATOR_ALREADY_HAS_OPEN_CASH_REGISTER",
            status_code=409,
        )


class SplitAmountMismatchException(BaseDomainException):
    """Disparada quando a soma das parcelas de um pagamento não fecha o total esperado."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, code="SPLIT_AMOUNT_MISMATCH", status_code=422)


class PublicApiRateLimitExceededError(BaseDomainException):
    """Disparada quando a rota pública de autoatendimento (`customer-checkout`)
    excede o teto de requisições da janela (docs/SECURITY.md §2.7)."""

    def __init__(self, retry_after_seconds: int) -> None:
        super().__init__(
            message="Muitas requisições. Tente novamente em instantes.",
            code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details={"retry_after_seconds": retry_after_seconds},
        )


class InvalidTableSecretException(BaseDomainException):
    """Disparada no autoatendimento do cliente (US-05.4) quando a secret de
    QR Code da mesa é ausente, incorreta ou expirada — mesmo princípio do
    `InvalidOrExpiredQrSecretError` do `dining-service`, replicado aqui
    porque é este serviço quem autoriza o pagamento sem papel de equipe."""

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


class PayableAmountUnavailableException(BaseDomainException):
    """Disparada quando o valor real de uma comanda não pôde ser confirmado
    contra `order-service`/`restaurant-service` (indisponibilidade,
    timeout) — falha fechada: nunca aprova um pagamento sem confirmar o
    valor de verdade (revisão de segurança, 2026-08-10)."""

    def __init__(self) -> None:
        super().__init__(
            message="Não foi possível confirmar o valor da comanda agora. Tente novamente em instantes.",
            code="PAYABLE_AMOUNT_UNAVAILABLE",
            status_code=503,
        )


class NoPayableOrdersError(BaseDomainException):
    """Disparada ao tentar pagar uma comanda sem nenhum pedido cobrável
    (vazia, ou só com pedidos cancelados)."""

    def __init__(self) -> None:
        super().__init__(
            message="Esta comanda não tem nenhum pedido para pagar.",
            code="NO_PAYABLE_ORDERS",
            status_code=409,
        )


class UnderpaidCommandException(BaseDomainException):
    """Disparada quando um pagamento da equipe declara um `expected_total`
    menor que a soma real dos pedidos não cancelados da comanda — piso de
    segurança pro fluxo autenticado (garçom/caixa), que continua livre pra
    cobrar mais que o piso (ex: gorjeta) mas nunca menos."""

    def __init__(self, *, declared: float, minimum: float) -> None:
        super().__init__(
            message=(
                f"O total informado (R$ {declared:.2f}) é menor que o total real "
                f"dos pedidos desta comanda (R$ {minimum:.2f})."
            ),
            code="UNDERPAID_COMMAND",
            status_code=422,
            details={"declared_total": declared, "minimum_total": minimum},
        )
