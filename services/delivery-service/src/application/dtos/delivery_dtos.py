"""DTOs (Pydantic v2) de Request/Response do serviço de Delivery.

Todo DTO de escrita usa `extra="forbid"` (docs/SECURITY.md §2.5).
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field
from src.domain.entities.delivery import DeliveryStatus


class CreateDeliveryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    order_id: uuid.UUID
    delivery_address: str = Field(..., min_length=1, max_length=500)


class AssignCourierRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    courier_name: str = Field(..., min_length=1, max_length=150)


class UpdateDeliveryStatusRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    new_status: DeliveryStatus


class DeliveryResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    order_id: uuid.UUID
    delivery_address: str
    courier_name: str | None
    status: DeliveryStatus
