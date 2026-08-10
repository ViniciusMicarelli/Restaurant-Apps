"""Casos de uso: consulta de um caixa e seu histórico de movimentações (US-05.3)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from restaurant_core.exceptions import ResourceNotFoundException
from src.application.dtos.payment_dtos import CashMovementResponse, CashRegisterResponse
from src.application.interfaces.repository_interface import (
    CashMovementRepositoryInterface,
    CashRegisterRepositoryInterface,
)
from src.application.use_cases._shared import to_cash_movement_response, to_cash_register_response


@dataclass
class GetCashRegisterUseCase:
    cash_register_repository: CashRegisterRepositoryInterface

    async def execute(self, *, cash_register_id: uuid.UUID) -> CashRegisterResponse:
        register = await self.cash_register_repository.get_by_id(cash_register_id)
        if register is None:
            raise ResourceNotFoundException("CashRegister", str(cash_register_id))
        return to_cash_register_response(register)


@dataclass
class GetMyOpenCashRegisterUseCase:
    """Caixa aberto do operador logado, se houver — usado pelo admin-web para
    saber em qual caixa lançar o pagamento sem o usuário precisar saber o ID."""

    cash_register_repository: CashRegisterRepositoryInterface

    async def execute(self, *, operator_id: uuid.UUID) -> CashRegisterResponse | None:
        register = await self.cash_register_repository.get_open_by_operator(operator_id)
        return to_cash_register_response(register) if register is not None else None


@dataclass
class ListCashMovementsUseCase:
    cash_movement_repository: CashMovementRepositoryInterface

    async def execute(self, *, cash_register_id: uuid.UUID) -> list[CashMovementResponse]:
        movements = await self.cash_movement_repository.list_by_register(cash_register_id)
        return [to_cash_movement_response(m) for m in movements]
