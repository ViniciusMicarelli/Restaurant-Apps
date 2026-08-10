"""Cliente HTTP para o `dining-service` — autoriza o endpoint público de
autoatendimento do cliente (US-05.4) validando a secret de QR Code da mesa
E devolvendo a comanda aberta de verdade (não é só um booleano de
validação: `command_id`/`service_fee_charged` viram a fonte de verdade
usada por `CustomerCheckoutUseCase` em vez do que o cliente mandar no
corpo da requisição — ver docs/logs/2026-08-10.md, revisão de segurança).
"""

from __future__ import annotations

import uuid

from src.application.interfaces.repository_interface import OpenCommandInfo
from src.infrastructure.clients._http import get_json


class HttpxDiningServiceClient:
    def __init__(self, base_url: str, timeout_seconds: float = 5.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    async def get_open_command_for_table(
        self, *, tenant_id: uuid.UUID, table_number: int, secret: str
    ) -> OpenCommandInfo | None:
        """`None` se a secret for inválida/expirada OU não houver comanda
        aberta pra essa mesa — mesmo tratamento pros dois casos: do lado do
        pagamento, ambos significam "não posso autorizar isso agora"
        (não vale a pena diferenciar e arriscar vazar qual dos dois é,
        mesmo princípio de mensagens genéricas do docs/SECURITY.md §2.7)."""
        url = f"{self._base_url}/api/v1/dining/tables/{table_number}/open-command"
        body = await get_json(
            url,
            params={"secret": secret},
            headers={"X-Tenant-Id": str(tenant_id)},
            timeout_seconds=self._timeout_seconds,
        )
        if body is None:
            return None
        return OpenCommandInfo(
            command_id=uuid.UUID(body["id"]),
            service_fee_charged=bool(body["service_fee_charged"]),
        )
