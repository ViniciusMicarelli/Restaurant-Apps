"""Caso de uso: consulta de um pagamento."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from restaurant_core.exceptions import ResourceNotFoundException
from src.application.dtos.payment_dtos import PaymentResponse
from src.application.interfaces.repository_interface import PaymentRepositoryInterface
from src.application.use_cases._shared import to_payment_response
from src.domain.entities.payment import PaymentStatus


@dataclass
class GetPaymentUseCase:
    payment_repository: PaymentRepositoryInterface

    async def execute(self, *, payment_id: uuid.UUID) -> PaymentResponse:
        payment = await self.payment_repository.get_by_id(payment_id)
        if payment is None:
            raise ResourceNotFoundException("Payment", str(payment_id))
        return to_payment_response(payment)


@dataclass
class ListPaymentsUseCase:
    payment_repository: PaymentRepositoryInterface

    async def execute(
        self, *, status: PaymentStatus | None = None, command_id: uuid.UUID | None = None
    ) -> list[PaymentResponse]:
        payments = await self.payment_repository.list_all(status=status, command_id=command_id)
        return [to_payment_response(p) for p in payments]
