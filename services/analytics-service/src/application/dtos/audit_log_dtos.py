"""DTOs (Pydantic v2) de Response do serviço de Analytics & Auditoria.

Sem DTOs de escrita: `AuditLog` só nasce a partir de eventos de domínio
consumidos (docs/ai/patterns.md), nunca via requisição HTTP direta.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    event_id: uuid.UUID
    event_type: str
    payload: dict[str, Any]
    occurred_at: datetime
