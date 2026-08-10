"""Caso de uso: fechamento cego de caixa, com relatório de divergência (US-05.3)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from restaurant_core.exceptions import ResourceNotFoundException
from src.application.dtos.payment_dtos import CashRegisterResponse
from src.application.interfaces.repository_interface import CashRegisterRepositoryInterface
from src.application.use_cases._shared import to_cash_register_response
from src.domain.exceptions import CashOperationException


@dataclass
class CloseCashRegisterUseCase:
    cash_register_repository: CashRegisterRepositoryInterface

    async def execute(
        self, *, cash_register_id: uuid.UUID, counted_amount: float
    ) -> CashRegisterResponse:
        register = await self.cash_register_repository.get_by_id(cash_register_id)
        if register is None:
            raise ResourceNotFoundException("CashRegister", str(cash_register_id))

        try:
            register.close(counted_amount)
        except ValueError as exc:
            raise CashOperationException(str(exc)) from exc

        saved = await self.cash_register_repository.save(register)
        return to_cash_register_response(saved)
