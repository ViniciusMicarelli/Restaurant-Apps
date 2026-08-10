"""Contratos de repositório e infraestrutura do serviço de Pagamentos e Caixa."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Protocol

from src.domain.entities.cash_movement import CashMovement
from src.domain.entities.cash_register import CashRegister
from src.domain.entities.payment import Payment, PaymentStatus


@dataclass(frozen=True)
class OpenCommandInfo:
    command_id: uuid.UUID
    service_fee_charged: bool


@dataclass(frozen=True)
class PayableSummary:
    """`total_amount`: soma dos pedidos NÃO cancelados da comanda.
    `reference_order_id`: primeiro pedido cobrável, usado como referência
    legada em `Payment.order_id` (compatibilidade — `Payment.command_id` é
    quem de fato identifica a comanda paga). `None` se não houver nenhum
    pedido cobrável (comanda vazia ou só com pedidos cancelados)."""

    total_amount: float
    reference_order_id: uuid.UUID | None


class CashRegisterRepositoryInterface(Protocol):
    async def get_by_id(self, cash_register_id: uuid.UUID) -> CashRegister | None: ...

    async def get_open_by_operator(self, operator_id: uuid.UUID) -> CashRegister | None: ...

    async def add(self, cash_register: CashRegister) -> CashRegister: ...

    async def save(self, cash_register: CashRegister) -> CashRegister: ...


class CashMovementRepositoryInterface(Protocol):
    """Append-only — auditoria de movimentações de caixa."""

    async def add(self, movement: CashMovement) -> CashMovement: ...

    async def list_by_register(self, cash_register_id: uuid.UUID) -> list[CashMovement]: ...


class PaymentRepositoryInterface(Protocol):
    async def get_by_id(self, payment_id: uuid.UUID) -> Payment | None: ...

    async def list_all(
        self, *, status: PaymentStatus | None = None, command_id: uuid.UUID | None = None
    ) -> list[Payment]: ...

    async def add(self, payment: Payment) -> Payment: ...


class DiningServiceClientInterface(Protocol):
    """Autoriza o autoatendimento do cliente (US-05.4) validando a secret de
    QR Code da mesa contra o `dining-service` E devolvendo a comanda aberta
    de verdade (docs/ai/architecture.md #1 permite REST síncrono entre
    microsserviços) — `command_id`/`service_fee_charged` viram a fonte de
    verdade usada por `CustomerCheckoutUseCase`, nunca o que o cliente
    mandar no corpo da requisição (revisão de segurança, 2026-08-10)."""

    async def get_open_command_for_table(
        self, *, tenant_id: uuid.UUID, table_number: int, secret: str
    ) -> OpenCommandInfo | None: ...


class OrderServiceClientInterface(Protocol):
    """Fonte de verdade do valor devido por uma comanda — nunca o
    `expected_total` que o cliente mandar."""

    async def get_payable_summary_for_command(
        self, *, tenant_id: uuid.UUID, command_id: uuid.UUID
    ) -> PayableSummary | None: ...


class RestaurantServiceClientInterface(Protocol):
    """Taxa de serviço real do tenant, pra compor o total autoritativo de
    uma comanda com `service_fee_charged=True`."""

    async def get_service_fee_percent(self, *, tenant_id: uuid.UUID) -> float | None: ...


class IdempotencyStoreInterface(Protocol):
    """Armazenamento de chaves de idempotência (Redis — docs/DATABASE.md).

    Evita que reenvios de rede (timeout + retry do cliente) processem o
    mesmo pagamento duas vezes: a mesma `Idempotency-Key` sempre retorna o
    `payment_id` já criado na primeira tentativa.
    """

    async def get_payment_id(self, idempotency_key: str) -> uuid.UUID | None: ...

    async def set_payment_id(
        self, idempotency_key: str, payment_id: uuid.UUID, ttl_seconds: int = 86400
    ) -> None: ...
