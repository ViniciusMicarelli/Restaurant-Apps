"""Cliente HTTP para o `order-service` — fonte de verdade do valor
efetivamente devido por uma comanda (nunca o `expected_total` que o
cliente mandar no corpo da requisição de pagamento). Ver
docs/logs/2026-08-10.md, revisão de segurança: o `payment-service` nunca
confiava nesse valor antes desta correção.
"""

from __future__ import annotations

import uuid

from src.application.interfaces.repository_interface import PayableSummary
from src.infrastructure.clients._http import get_json

_CANCELLED_STATUS = "CANCELLED"


class HttpxOrderServiceClient:
    def __init__(self, base_url: str, timeout_seconds: float = 5.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    async def get_payable_summary_for_command(
        self, *, tenant_id: uuid.UUID, command_id: uuid.UUID
    ) -> PayableSummary | None:
        """`None` em falha de rede/status inesperado do `order-service` —
        autoatendimento e conferência do garçom falham fechado nesse caso,
        nunca aprovam um pagamento sem confirmar o valor real."""
        url = f"{self._base_url}/api/v1/orders"
        body = await get_json(
            url,
            params={"command_id": str(command_id)},
            headers={"X-Tenant-Id": str(tenant_id)},
            timeout_seconds=self._timeout_seconds,
        )
        if body is None:
            return None

        payable_orders = [order for order in body if order["status"] != _CANCELLED_STATUS]
        if not payable_orders:
            return PayableSummary(total_amount=0.0, reference_order_id=None)

        total = round(sum(float(order["total_amount"]) for order in payable_orders), 2)
        reference_order_id = uuid.UUID(payable_orders[0]["id"])
        return PayableSummary(total_amount=total, reference_order_id=reference_order_id)
