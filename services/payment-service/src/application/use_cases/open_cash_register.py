"""Caso de uso: abertura de caixa operacional com suprimento inicial (US-05.1)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from restaurant_core.ids import generate_uuid7
from src.application.dtos.payment_dtos import CashRegisterResponse
from src.application.interfaces.repository_interface import (
    CashMovementRepositoryInterface,
    CashRegisterRepositoryInterface,
)
from src.application.use_cases._shared import to_cash_register_response
from src.domain.entities.cash_movement import CashMovement, CashMovementType
from src.domain.entities.cash_register import CashRegister
from src.domain.exceptions import OperatorAlreadyHasOpenCashRegisterException


@dataclass
class OpenCashRegisterUseCase:
    cash_register_repository: CashRegisterRepositoryInterface
    cash_movement_repository: CashMovementRepositoryInterface

    async def execute(
        self, *, tenant_id: uuid.UUID, operator_id: uuid.UUID, opening_amount: float
    ) -> CashRegisterResponse:
        already_open = await self.cash_register_repository.get_open_by_operator(operator_id)
        if already_open is not None:
            raise OperatorAlreadyHasOpenCashRegisterException(str(operator_id))

        register = CashRegister(
            id=generate_uuid7(),
            tenant_id=tenant_id,
            operator_id=operator_id,
            opening_amount=opening_amount,
            current_balance=opening_amount,
        )
        created = await self.cash_register_repository.add(register)

        await self.cash_movement_repository.add(
            CashMovement(
                id=generate_uuid7(),
                tenant_id=tenant_id,
                cash_register_id=created.id,
                movement_type=CashMovementType.OPENING_FLOAT,
                amount_delta=opening_amount,
            )
        )
        return to_cash_register_response(created)
