"""Caso de uso: pagamento de autoatendimento do cliente pelo `customer-web`
(US-05.4) — sem caixa/operador, autorizado pela secret de QR Code da mesa em
vez de um papel de equipe.

Nota de segurança (2026-08-10): o `command_id` e o valor total a cobrar são
**sempre computados aqui**, consultando `dining-service` (comanda aberta de
verdade) e `order-service`/`restaurant-service` (total real dos pedidos +
taxa de serviço) — nunca aceitos do corpo da requisição do cliente. Antes
desta correção, um cliente com uma secret de mesa válida (a própria)
conseguia forjar `order_id`/`command_id`/`expected_total` e pagar qualquer
valor por qualquer comanda do tenant.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from src.application.dtos.payment_dtos import PaymentResponse, PaymentSplitRequest
from src.application.interfaces.repository_interface import (
    DiningServiceClientInterface,
    OrderServiceClientInterface,
    RestaurantServiceClientInterface,
)
from src.application.use_cases.process_payment import ProcessPaymentUseCase
from src.domain.exceptions import (
    InvalidTableSecretException,
    NoPayableOrdersError,
    PayableAmountUnavailableException,
)


@dataclass
class CustomerCheckoutUseCase:
    process_payment_use_case: ProcessPaymentUseCase
    dining_service_client: DiningServiceClientInterface
    order_service_client: OrderServiceClientInterface
    restaurant_service_client: RestaurantServiceClientInterface

    async def execute(  # noqa: PLR0913 - parâmetros nomeados (keyword-only) mapeando 1:1 com o DTO de entrada
        self,
        *,
        tenant_id: uuid.UUID,
        table_number: int,
        secret: str,
        splits: list[PaymentSplitRequest],
        idempotency_key: str | None,
        card_last4: str | None,
        card_holder_name: str | None,
    ) -> PaymentResponse:
        command_info = await self.dining_service_client.get_open_command_for_table(
            tenant_id=tenant_id, table_number=table_number, secret=secret
        )
        if command_info is None:
            raise InvalidTableSecretException(table_number)

        summary = await self.order_service_client.get_payable_summary_for_command(
            tenant_id=tenant_id, command_id=command_info.command_id
        )
        if summary is None:
            raise PayableAmountUnavailableException()
        if summary.total_amount <= 0 or summary.reference_order_id is None:
            raise NoPayableOrdersError()

        total = summary.total_amount
        if command_info.service_fee_charged:
            fee_percent = await self.restaurant_service_client.get_service_fee_percent(
                tenant_id=tenant_id
            )
            if fee_percent is None:
                raise PayableAmountUnavailableException()
            total = round(total * (1 + fee_percent / 100), 2)

        return await self.process_payment_use_case.execute(
            tenant_id=tenant_id,
            order_id=summary.reference_order_id,
            cash_register_id=None,
            command_id=command_info.command_id,
            expected_total=total,
            splits=splits,
            idempotency_key=idempotency_key,
            card_last4=card_last4,
            card_holder_name=card_holder_name,
            signature_data=None,
        )
