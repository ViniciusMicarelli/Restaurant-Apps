"""Caso de uso: pagamento processado pela equipe (garçom/caixa), com um piso
de segurança quando `command_id` é informado (US-05.2 + revisão de
segurança de 2026-08-10).

`ProcessPaymentUseCase` continua confiando no `expected_total` recebido —
esse comportamento é mantido de propósito pro caminho de pedido avulso sem
comanda (`command_id=None`), onde não há hoje nenhuma fonte server-side pra
cruzar o valor. Quando `command_id` vem preenchido (é o caso de 100% dos
pagamentos da equipe hoje, via `CheckoutModal.tsx` do `admin-web`), este
wrapper confere o total real dos pedidos da comanda no `order-service` e
rejeita qualquer `expected_total` menor que esse piso — a equipe continua
livre pra cobrar mais (ex: gorjeta), nunca menos.

Não confere a taxa de serviço com a mesma precisão do autoatendimento do
cliente (`CustomerCheckoutUseCase`) — a equipe já vê/controla o toggle de
taxa de serviço na própria tela antes de cobrar, e o pagamento é
autenticado + RBAC + auditável, um risco residual bem menor que o do
endpoint público. Ver docs/logs/2026-08-10.md.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from src.application.dtos.payment_dtos import PaymentResponse, PaymentSplitRequest
from src.application.interfaces.repository_interface import OrderServiceClientInterface
from src.application.use_cases.process_payment import ProcessPaymentUseCase
from src.domain.exceptions import PayableAmountUnavailableException, UnderpaidCommandException

_ROUNDING_TOLERANCE = 0.01


@dataclass
class StaffCheckoutUseCase:
    process_payment_use_case: ProcessPaymentUseCase
    order_service_client: OrderServiceClientInterface

    async def execute(  # noqa: PLR0913 - parâmetros nomeados (keyword-only) mapeando 1:1 com o DTO de entrada
        self,
        *,
        tenant_id: uuid.UUID,
        order_id: uuid.UUID,
        cash_register_id: uuid.UUID,
        command_id: uuid.UUID | None,
        expected_total: float,
        splits: list[PaymentSplitRequest],
        idempotency_key: str | None,
        card_last4: str | None,
        card_holder_name: str | None,
        signature_data: str | None,
    ) -> PaymentResponse:
        if command_id is not None:
            summary = await self.order_service_client.get_payable_summary_for_command(
                tenant_id=tenant_id, command_id=command_id
            )
            if summary is None:
                raise PayableAmountUnavailableException()
            if expected_total + _ROUNDING_TOLERANCE < summary.total_amount:
                raise UnderpaidCommandException(
                    declared=expected_total, minimum=summary.total_amount
                )

        return await self.process_payment_use_case.execute(
            tenant_id=tenant_id,
            order_id=order_id,
            cash_register_id=cash_register_id,
            command_id=command_id,
            expected_total=expected_total,
            splits=splits,
            idempotency_key=idempotency_key,
            card_last4=card_last4,
            card_holder_name=card_holder_name,
            signature_data=signature_data,
        )
