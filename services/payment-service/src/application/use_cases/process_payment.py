"""Caso de uso: processamento do pagamento de uma comanda (US-05.2), com idempotência real.

A chave de idempotência é armazenada em Redis (não apenas ecoada de volta):
reenvios de rede com a mesma `Idempotency-Key` sempre retornam o mesmo
`Payment` já criado na primeira tentativa, sem processar a cobrança de novo.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from restaurant_core.exceptions import ResourceNotFoundException
from restaurant_core.ids import generate_uuid7
from src.application.dtos.payment_dtos import PaymentResponse, PaymentSplitRequest
from src.application.interfaces.repository_interface import (
    CashMovementRepositoryInterface,
    CashRegisterRepositoryInterface,
    IdempotencyStoreInterface,
    PaymentRepositoryInterface,
)
from src.application.use_cases._shared import to_payment_response
from src.domain.entities.cash_movement import CashMovement, CashMovementType
from src.domain.entities.payment import Payment, PaymentSplit
from src.domain.entities.payment_method import PaymentMethod
from src.domain.exceptions import CashOperationException, SplitAmountMismatchException


@dataclass
class ProcessPaymentUseCase:
    payment_repository: PaymentRepositoryInterface
    cash_register_repository: CashRegisterRepositoryInterface
    cash_movement_repository: CashMovementRepositoryInterface
    idempotency_store: IdempotencyStoreInterface

    async def execute(  # noqa: PLR0913 - parâmetros nomeados (keyword-only) mapeando 1:1 com o DTO de entrada
        self,
        *,
        tenant_id: uuid.UUID,
        order_id: uuid.UUID,
        cash_register_id: uuid.UUID | None,
        expected_total: float,
        splits: list[PaymentSplitRequest],
        command_id: uuid.UUID | None = None,
        idempotency_key: str | None = None,
        card_last4: str | None = None,
        card_holder_name: str | None = None,
        signature_data: str | None = None,
    ) -> PaymentResponse:
        if idempotency_key:
            existing_payment_id = await self.idempotency_store.get_payment_id(idempotency_key)
            if existing_payment_id is not None:
                existing_payment = await self.payment_repository.get_by_id(existing_payment_id)
                if existing_payment is not None:
                    return to_payment_response(existing_payment)

        domain_splits = [
            PaymentSplit(payment_method=s.payment_method, amount=s.amount) for s in splits
        ]
        has_cash_split = any(s.payment_method == PaymentMethod.CASH for s in domain_splits)
        if cash_register_id is None:
            # Autoatendimento do cliente (US-05.4) — sem operador/caixa físico,
            # então dinheiro nunca é uma opção válida nesse canal.
            if has_cash_split:
                raise CashOperationException(
                    "Pagamento em dinheiro exige um caixa operacional aberto."
                )
            register = None
        else:
            register = await self.cash_register_repository.get_by_id(cash_register_id)
            if register is None:
                raise ResourceNotFoundException("CashRegister", str(cash_register_id))

        payment = Payment(
            id=generate_uuid7(),
            tenant_id=tenant_id,
            order_id=order_id,
            cash_register_id=cash_register_id,
            command_id=command_id,
            splits=domain_splits,
            idempotency_key=idempotency_key,
            card_last4=card_last4,
            card_holder_name=card_holder_name,
            signature_data=signature_data,
        )

        try:
            payment.assert_splits_match_expected_total(expected_total)
        except ValueError as exc:
            raise SplitAmountMismatchException(str(exc)) from exc

        cash_amount = payment.cash_amount
        if register is not None and cash_amount > 0:
            try:
                register.apply_cash_movement(cash_amount)
            except ValueError as exc:
                raise CashOperationException(str(exc)) from exc
            await self.cash_register_repository.save(register)

        created = await self.payment_repository.add(payment)

        if register is not None and cash_amount > 0:
            await self.cash_movement_repository.add(
                CashMovement(
                    id=generate_uuid7(),
                    tenant_id=tenant_id,
                    cash_register_id=register.id,
                    movement_type=CashMovementType.SALE,
                    amount_delta=cash_amount,
                    payment_id=created.id,
                )
            )

        if idempotency_key:
            await self.idempotency_store.set_payment_id(idempotency_key, created.id)

        return to_payment_response(created)
