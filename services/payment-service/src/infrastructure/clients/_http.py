"""Helper HTTP compartilhado pelos clientes REST síncronos deste serviço
(docs/ai/architecture.md #1 permite REST síncrono entre microsserviços).
GET simples com timeout curto — qualquer erro de rede/timeout ou status
diferente de 200 vira `None`, nunca uma exceção propagada: cada client
decide o que "não consegui confirmar" significa pro seu caso de uso (falha
fechada, sempre — nenhum destes clients aprova algo sem confirmação).
"""

from __future__ import annotations

from typing import Any

import httpx


async def get_json(
    url: str,
    *,
    params: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    timeout_seconds: float = 5.0,
) -> Any | None:
    try:
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            response = await client.get(url, params=params, headers=headers)
    except httpx.HTTPError:
        return None
    if response.status_code != httpx.codes.OK:
        return None
    return response.json()
