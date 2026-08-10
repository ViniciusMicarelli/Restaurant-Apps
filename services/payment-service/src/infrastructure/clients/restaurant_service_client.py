"""Cliente HTTP para o `restaurant-service` — taxa de serviço real do
tenant, usada para compor o total autoritativo de uma comanda com
`service_fee_charged=True` (nunca aceita a taxa "embutida" no
`expected_total` que o cliente mandar).
"""

from __future__ import annotations

import uuid

from src.infrastructure.clients._http import get_json


class HttpxRestaurantServiceClient:
    def __init__(self, base_url: str, timeout_seconds: float = 5.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    async def get_service_fee_percent(self, *, tenant_id: uuid.UUID) -> float | None:
        """`GET /api/v1/restaurants/{id}` é público (sem X-Tenant-Id nem
        JWT) — `restaurant_id` já É o `tenant_id` neste projeto. `None` em
        falha de rede/status inesperado."""
        url = f"{self._base_url}/api/v1/restaurants/{tenant_id}"
        body = await get_json(url, timeout_seconds=self._timeout_seconds)
        if body is None:
            return None
        return float(body["service_fee_percent"])
