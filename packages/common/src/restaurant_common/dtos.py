"""DTOs compartilhados entre microsserviços (comunicação inter-serviço e respostas comuns)."""

from __future__ import annotations

import uuid

from pydantic import BaseModel


class TenantContextDTO(BaseModel):
    """Payload mínimo trocado entre serviços para identificar o tenant/ator de uma requisição."""

    model_config = {"extra": "forbid"}

    tenant_id: uuid.UUID
    user_id: uuid.UUID
    role: str


class HealthResponse(BaseModel):
    """Corpo padrão do endpoint `/health` de todos os microsserviços."""

    status: str = "healthy"
    service: str
