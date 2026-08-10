"""Entidades `Payment`/`PaymentSplit` — pagamento de uma comanda, com divisão entre
meios de pagamento (US-05.2: "selecionar as formas de pagamento")."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from src.domain.entities.payment_method import PaymentMethod

_ROUNDING_TOLERANCE = 0.01


class PaymentStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


@dataclass
class PaymentSplit:
    """Uma parcela do pagamento em um meio específico (ex: metade Pix, metade Cartão)."""

    payment_method: PaymentMethod
    amount: float

    def __post_init__(self) -> None:
        if self.amount <= 0:
            raise ValueError("O valor de uma parcela de pagamento deve ser positivo.")


@dataclass
class Payment:
    """Pagamento de uma comanda/pedido, possivelmente dividido entre meios (Aggregate Root).

    Attributes:
        id: UUIDv7 do pagamento.
        tenant_id: ID do restaurante proprietário.
        order_id: ID de um pedido do `order-service` associado ao pagamento.
            Numa comanda com múltiplos pedidos, referencia só um deles
            (histórico — mantido por compatibilidade) — quando `command_id`
            está presente, ele é a referência autoritativa de "a qual
            comanda este pagamento pertence", não `order_id`.
        command_id: ID da comanda do `dining-service` paga por inteiro
            (refatoração "Payment por Comanda"). `None` em pagamentos de
            pedido avulso sem comanda (ex: futuro balcão/delivery, Fase 3
            do roadmap) e em registros anteriores a esta mudança.
        cash_register_id: Caixa operacional que processou o pagamento. `None`
            para pagamentos de autoatendimento do cliente (US-05.4,
            `customer-web`) — não existe operador/caixa físico nesse canal,
            só cartão/Pix simulados (nunca dinheiro).
        splits: Parcelas do pagamento por meio (a soma deve fechar `total_amount`).
        status: Estado atual do pagamento.
        idempotency_key: Chave que evita duplo processamento em retentativas de rede.
        card_last4: Últimos 4 dígitos do cartão informado (pagamento simulado —
            nunca persiste o PAN completo nem o CVV, mesmo em modo fake).
        card_holder_name: Nome impresso no cartão informado, para recibo.
        signature_data: Assinatura do cliente capturada na tela (PNG em base64),
            evidência de conferência/aceite da comanda no fechamento.
        created_at: Quando o pagamento foi processado — base do histórico de
            pagamentos no dashboard do dono (`GET /payments`, já ordenado por
            este campo, só nunca tinha ido para o contrato da API).
    """

    id: uuid.UUID
    tenant_id: uuid.UUID
    order_id: uuid.UUID
    cash_register_id: uuid.UUID | None = None
    command_id: uuid.UUID | None = None
    splits: list[PaymentSplit] = field(default_factory=list)
    status: PaymentStatus = PaymentStatus.APPROVED
    idempotency_key: str | None = None
    card_last4: str | None = None
    card_holder_name: str | None = None
    signature_data: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if not self.splits:
            raise ValueError("Um pagamento deve conter ao menos uma parcela (split).")

    @property
    def total_amount(self) -> float:
        return round(sum(split.amount for split in self.splits), 2)

    @property
    def cash_amount(self) -> float:
        """Soma das parcelas pagas em dinheiro — único meio que movimenta o caixa físico."""
        return round(
            sum(s.amount for s in self.splits if s.payment_method == PaymentMethod.CASH), 2
        )

    def assert_splits_match_expected_total(self, expected_total: float) -> None:
        """Valida que a soma das parcelas fecha o valor esperado da comanda.

        Raises:
            ValueError: Se a soma dos splits divergir do total esperado além
                da tolerância de arredondamento (1 centavo).
        """
        if abs(self.total_amount - round(expected_total, 2)) > _ROUNDING_TOLERANCE:
            raise ValueError(
                f"A soma das parcelas ({self.total_amount}) não corresponde ao "
                f"total esperado da comanda ({round(expected_total, 2)})."
            )
