"""Helpers compartilhados entre casos de uso do serviço de Marketing."""

from __future__ import annotations

from src.application.dtos.marketing_dtos import CouponResponse
from src.domain.entities.coupon import Coupon


def to_coupon_response(coupon: Coupon) -> CouponResponse:
    return CouponResponse(
        id=coupon.id,
        tenant_id=coupon.tenant_id,
        code=coupon.code,
        discount_type=coupon.discount_type,
        discount_value=coupon.discount_value,
        valid_from=coupon.valid_from,
        valid_until=coupon.valid_until,
        max_uses=coupon.max_uses,
        times_used=coupon.times_used,
        active=coupon.active,
    )
