"""DTOs (Pydantic v2) de Request/Response do serviço de Pagamentos e Caixa.

Todo DTO de escrita usa `extra="forbid"` (docs/SECURITY.md §2.5).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from src.domain.entities.cash_movement import CashMovementType
from src.domain.entities.cash_register import CashRegisterStatus
from src.domain.entities.payment import PaymentStatus
from src.domain.entities.payment_method import PaymentMethod


class OpenCashRegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operator_id: uuid.UUID
    opening_amount: float = Field(..., ge=0)


class CloseCashRegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    counted_amount: float = Field(..., ge=0)


class RegisterCashMovementRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    movement_type: CashMovementType
    amount: float = Field(..., gt=0)
    reason: str | None = Field(default=None, max_length=500)


class CashRegisterResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    operator_id: uuid.UUID
    opening_amount: float
    current_balance: float
    status: CashRegisterStatus
    opened_at: datetime
    closed_at: datetime | None
    closing_counted_amount: float | None
    closing_divergence: float | None


class CashMovementResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    cash_register_id: uuid.UUID
    movement_type: CashMovementType
    amount_delta: float
    reason: str | None
    payment_id: uuid.UUID | None
    created_at: datetime


class PaymentSplitRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    payment_method: PaymentMethod
    amount: float = Field(..., gt=0)


class ProcessPaymentRequest(BaseModel):
    """Pagamento processado pela equipe (garçom/caixa) — sempre com um caixa
    operacional aberto por trás, mesmo em Pix/Cartão (accountability do
    turno). O autoatendimento do cliente sem caixa usa `CustomerCheckoutRequest`."""

    model_config = ConfigDict(extra="forbid")

    order_id: uuid.UUID
    cash_register_id: uuid.UUID
    # Referência autoritativa da comanda paga, quando o pagamento fecha uma
    # comanda inteira (pode ter vários pedidos) em vez de um pedido avulso —
    # "Payment por Comanda". `order_id` continua obrigatório por
    # compatibilidade, mas deixa de ser a fonte de verdade quando este campo
    # vem preenchido.
    command_id: uuid.UUID | None = None
    expected_total: float = Field(..., gt=0)
    splits: list[PaymentSplitRequest] = Field(..., min_length=1)
    # Pagamento simulado (docs/ai/patterns.md — Tier B, sem gateway real):
    # só os 4 últimos dígitos do cartão chegam a ser recebidos, o PAN
    # completo e o CVV nunca saem do formulário do cliente (nem em modo fake).
    card_last4: str | None = Field(default=None, min_length=4, max_length=4, pattern=r"^\d{4}$")
    card_holder_name: str | None = Field(default=None, max_length=150)
    signature_data: str | None = Field(default=None, max_length=200_000)


class PaymentSplitResponse(BaseModel):
    payment_method: PaymentMethod
    amount: float


class CustomerCheckoutRequest(BaseModel):
    """Pagamento de autoatendimento do cliente pelo `customer-web` (US-05.4) —
    sem JWT, autorizado pela secret de QR Code da própria mesa em vez de um
    papel de equipe/caixa aberto.

    Nota de segurança (2026-08-10): `order_id`/`command_id`/`expected_total`
    NUNCA vêm do cliente — o servidor descobre a comanda aberta e o valor
    real dos pedidos consultando `dining-service`/`order-service`/
    `restaurant-service` (ver `CustomerCheckoutUseCase`). Antes desta
    correção, um cliente com uma secret de mesa válida (a própria) podia
    forjar esses três campos e pagar qualquer valor por qualquer comanda.
    """

    model_config = ConfigDict(extra="forbid")

    table_number: int = Field(..., ge=1)
    secret: str = Field(..., min_length=1)
    # CASH nunca é aceito aqui (validado no use case) — pagamento remoto não
    # tem dinheiro físico envolvido. O valor de cada parcela ainda vem do
    # cliente (pra permitir split entre métodos no futuro), mas só é aceito
    # se a SOMA bater com o total computado no servidor.
    splits: list[PaymentSplitRequest] = Field(..., min_length=1)
    card_last4: str | None = Field(default=None, min_length=4, max_length=4, pattern=r"^\d{4}$")
    card_holder_name: str | None = Field(default=None, max_length=150)


class PaymentResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    order_id: uuid.UUID
    cash_register_id: uuid.UUID | None
    command_id: uuid.UUID | None
    splits: list[PaymentSplitResponse]
    total_amount: float
    status: PaymentStatus
    card_last4: str | None
    card_holder_name: str | None
    signature_data: str | None
    created_at: datetime
