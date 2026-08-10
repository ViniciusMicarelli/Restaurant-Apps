"""Caso de uso: movimentação manual de caixa (sangria, suprimento adicional)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from restaurant_core.exceptions import ResourceNotFoundException
from restaurant_core.ids import generate_uuid7
from src.application.dtos.payment_dtos import CashMovementResponse
from src.application.interfaces.repository_interface import (
    CashMovementRepositoryInterface,
    CashRegisterRepositoryInterface,
)
from src.application.use_cases._shared import to_cash_movement_response
from src.domain.entities.cash_movement import CashMovement, CashMovementType
from src.domain.exceptions import CashOperationException

_SIGNED_DELTA: dict[CashMovementType, int] = {
    CashMovementType.SUPPLY: 1,
    CashMovementType.SANGRIA: -1,
}


@dataclass
class RegisterCashMovementUseCase:
    cash_register_repository: CashRegisterRepositoryInterface
    cash_movement_repository: CashMovementRepositoryInterface

    async def execute(
        self,
        *,
        cash_register_id: uuid.UUID,
        movement_type: CashMovementType,
        amount: float,
        reason: str | None,
    ) -> CashMovementResponse:
        if movement_type not in _SIGNED_DELTA:
            raise CashOperationException(
                f"Tipo de movimentação '{movement_type.value}' não pode ser registrado manualmente."
            )
        if movement_type == CashMovementType.SANGRIA and not (reason and reason.strip()):
            raise CashOperationException("Toda sangria exige um motivo registrado para auditoria.")

        register = await self.cash_register_repository.get_by_id(cash_register_id)
        if register is None:
            raise ResourceNotFoundException("CashRegister", str(cash_register_id))

        delta = amount * _SIGNED_DELTA[movement_type]
        try:
            register.apply_cash_movement(delta)
        except ValueError as exc:
            raise CashOperationException(str(exc)) from exc

        await self.cash_register_repository.save(register)

        movement = await self.cash_movement_repository.add(
            CashMovement(
                id=generate_uuid7(),
                tenant_id=register.tenant_id,
                cash_register_id=register.id,
                movement_type=movement_type,
                amount_delta=delta,
                reason=reason,
            )
        )
        return to_cash_movement_response(movement)
