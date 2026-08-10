"""DTOs (Pydantic v2) de Request/Response do serviço de Cozinha/KDS.

Todo DTO de escrita usa `extra="forbid"` (docs/SECURITY.md §2.5).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from src.domain.entities.kds_item import KDSItemStatus, KDSStation


class UpdateKDSItemStatusRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    new_status: KDSItemStatus


class KDSItemResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    order_id: uuid.UUID
    product_id: uuid.UUID
    product_name: str
    quantity: int
    station: KDSStation
    table_number: int | None
    notes: str | None
    status: KDSItemStatus
    created_at: datetime
    ready_at: datetime | None
    delivered_at: datetime | None
