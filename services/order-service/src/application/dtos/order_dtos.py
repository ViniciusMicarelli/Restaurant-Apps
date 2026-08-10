"""DTOs (Pydantic v2) de Request/Response do serviço de Pedidos.

Todo DTO de escrita usa `extra="forbid"` (docs/SECURITY.md §2.5).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from src.domain.entities.order import OrderStatus, OrderType


class CreateOrderItemRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: uuid.UUID
    product_name: str = Field(..., min_length=1, max_length=150)
    unit_price: float = Field(..., ge=0)
    quantity: int = Field(default=1, ge=1)
    notes: str | None = Field(default=None, max_length=500)


class CreateOrderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    order_type: OrderType
    table_number: int | None = Field(default=None, ge=1)
    command_id: uuid.UUID | None = None
    items: list[CreateOrderItemRequest] = Field(..., min_length=1)


class CancelOrderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cancellation_reason: str = Field(..., min_length=3, max_length=500)


class TransitionOrderStatusRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    new_status: OrderStatus


class OrderItemResponse(BaseModel):
    product_id: uuid.UUID
    product_name: str
    unit_price: float
    quantity: int
    notes: str | None
    total_price: float


class OrderResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    order_type: OrderType
    table_number: int | None
    command_id: uuid.UUID | None
    status: OrderStatus
    items: list[OrderItemResponse]
    total_amount: float
    cancellation_reason: str | None
    created_at: datetime
