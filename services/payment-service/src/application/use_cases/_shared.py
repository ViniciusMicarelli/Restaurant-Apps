"""Helpers compartilhados entre casos de uso do serviço de Pagamentos e Caixa."""

from __future__ import annotations

from src.application.dtos.payment_dtos import (
    CashMovementResponse,
    CashRegisterResponse,
    PaymentResponse,
    PaymentSplitResponse,
)
from src.domain.entities.cash_movement import CashMovement
from src.domain.entities.cash_register import CashRegister
from src.domain.entities.payment import Payment


def to_cash_register_response(register: CashRegister) -> CashRegisterResponse:
    if register.opened_at is None:
        msg = "CashRegister.opened_at deveria estar sempre preenchido após __post_init__."
        raise RuntimeError(msg)
    return CashRegisterResponse(
        id=register.id,
        tenant_id=register.tenant_id,
        operator_id=register.operator_id,
        opening_amount=register.opening_amount,
        current_balance=register.current_balance,
        status=register.status,
        opened_at=register.opened_at,
        closed_at=register.closed_at,
        closing_counted_amount=register.closing_counted_amount,
        closing_divergence=register.closing_divergence,
    )


def to_cash_movement_response(movement: CashMovement) -> CashMovementResponse:
    return CashMovementResponse(
        id=movement.id,
        tenant_id=movement.tenant_id,
        cash_register_id=movement.cash_register_id,
        movement_type=movement.movement_type,
        amount_delta=movement.amount_delta,
        reason=movement.reason,
        payment_id=movement.payment_id,
        created_at=movement.created_at,
    )


def to_payment_response(payment: Payment) -> PaymentResponse:
    return PaymentResponse(
        id=payment.id,
        tenant_id=payment.tenant_id,
        order_id=payment.order_id,
        cash_register_id=payment.cash_register_id,
        command_id=payment.command_id,
        splits=[
            PaymentSplitResponse(payment_method=s.payment_method, amount=s.amount)
            for s in payment.splits
        ],
        total_amount=payment.total_amount,
        status=payment.status,
        card_last4=payment.card_last4,
        card_holder_name=payment.card_holder_name,
        signature_data=payment.signature_data,
        created_at=payment.created_at,
    )
