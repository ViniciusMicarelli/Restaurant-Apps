"""DTOs (Pydantic v2) de Request/Response do serviço de Marketing.

Todo DTO de escrita usa `extra="forbid"` (docs/SECURITY.md §2.5).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from src.domain.entities.coupon import DiscountType


class CreateCouponRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1, max_length=50)
    discount_type: DiscountType
    discount_value: float = Field(..., gt=0)
    valid_from: datetime
    valid_until: datetime
    max_uses: int | None = Field(default=None, ge=1)


class ApplyCouponRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1, max_length=50)
    order_total: float = Field(..., gt=0)


class CouponResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    code: str
    discount_type: DiscountType
    discount_value: float
    valid_from: datetime
    valid_until: datetime
    max_uses: int | None
    times_used: int
    active: bool


class ApplyCouponResponse(BaseModel):
    coupon: CouponResponse
    discount_amount: float
    final_total: float
