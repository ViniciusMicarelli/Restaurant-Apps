"""Fakes em memória dos contratos do `payment-service` — usados pelos testes unitários."""

from __future__ import annotations

import uuid

from src.application.interfaces.repository_interface import OpenCommandInfo, PayableSummary
from src.domain.entities.cash_movement import CashMovement
from src.domain.entities.cash_register import CashRegister, CashRegisterStatus
from src.domain.entities.payment import Payment, PaymentStatus


class FakeCashRegisterStore:
    def __init__(self, registers: list[CashRegister] | None = None) -> None:
        self._registers: dict[uuid.UUID, CashRegister] = {r.id: r for r in (registers or [])}

    async def get_by_id(self, cash_register_id: uuid.UUID) -> CashRegister | None:
        return self._registers.get(cash_register_id)

    async def get_open_by_operator(self, operator_id: uuid.UUID) -> CashRegister | None:
        for register in self._registers.values():
            if register.operator_id == operator_id and register.status == CashRegisterStatus.OPEN:
                return register
        return None

    async def add(self, cash_register: CashRegister) -> CashRegister:
        self._registers[cash_register.id] = cash_register
        return cash_register

    async def save(self, cash_register: CashRegister) -> CashRegister:
        self._registers[cash_register.id] = cash_register
        return cash_register


class FakeCashMovementStore:
    def __init__(self) -> None:
        self.movements: list[CashMovement] = []

    async def add(self, movement: CashMovement) -> CashMovement:
        self.movements.append(movement)
        return movement

    async def list_by_register(self, cash_register_id: uuid.UUID) -> list[CashMovement]:
        return [m for m in self.movements if m.cash_register_id == cash_register_id]


class FakePaymentStore:
    def __init__(self, payments: list[Payment] | None = None) -> None:
        self._payments: dict[uuid.UUID, Payment] = {p.id: p for p in (payments or [])}

    async def get_by_id(self, payment_id: uuid.UUID) -> Payment | None:
        return self._payments.get(payment_id)

    async def list_all(
        self, *, status: PaymentStatus | None = None, command_id: uuid.UUID | None = None
    ) -> list[Payment]:
        payments = list(self._payments.values())
        if status is not None:
            payments = [p for p in payments if p.status == status]
        if command_id is not None:
            payments = [p for p in payments if p.command_id == command_id]
        return payments

    async def add(self, payment: Payment) -> Payment:
        self._payments[payment.id] = payment
        return payment


class FakeDiningServiceClient:
    """Fake de `DiningServiceClientInterface` — evita bater no `dining-service`
    de verdade nos testes unitários do autoatendimento do cliente (US-05.4)."""

    def __init__(self, *, open_command: OpenCommandInfo | None) -> None:
        self.open_command = open_command
        self.calls: list[tuple[uuid.UUID, int, str]] = []

    async def get_open_command_for_table(
        self, *, tenant_id: uuid.UUID, table_number: int, secret: str
    ) -> OpenCommandInfo | None:
        self.calls.append((tenant_id, table_number, secret))
        return self.open_command


class FakeOrderServiceClient:
    """Fake de `OrderServiceClientInterface` — evita bater no `order-service`
    de verdade. `summary=None` simula indisponibilidade (falha fechada)."""

    def __init__(self, *, summary: PayableSummary | None) -> None:
        self.summary = summary
        self.calls: list[tuple[uuid.UUID, uuid.UUID]] = []

    async def get_payable_summary_for_command(
        self, *, tenant_id: uuid.UUID, command_id: uuid.UUID
    ) -> PayableSummary | None:
        self.calls.append((tenant_id, command_id))
        return self.summary


class FakeRestaurantServiceClient:
    """Fake de `RestaurantServiceClientInterface` — evita bater no
    `restaurant-service` de verdade. `fee_percent=None` simula indisponibilidade."""

    def __init__(self, *, fee_percent: float | None) -> None:
        self.fee_percent = fee_percent
        self.calls: list[uuid.UUID] = []

    async def get_service_fee_percent(self, *, tenant_id: uuid.UUID) -> float | None:
        self.calls.append(tenant_id)
        return self.fee_percent


class FakeIdempotencyStore:
    def __init__(self) -> None:
        self._store: dict[str, uuid.UUID] = {}

    async def get_payment_id(self, idempotency_key: str) -> uuid.UUID | None:
        return self._store.get(idempotency_key)

    async def set_payment_id(
        self, idempotency_key: str, payment_id: uuid.UUID, ttl_seconds: int = 86400
    ) -> None:
        del ttl_seconds
        self._store[idempotency_key] = payment_id
