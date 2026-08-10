"""Caso de uso: validação e aplicação de um cupom de desconto a um total de pedido."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from restaurant_core.exceptions import ResourceNotFoundException
from src.application.dtos.marketing_dtos import ApplyCouponResponse
from src.application.interfaces.repository_interface import CouponRepositoryInterface
from src.application.use_cases._shared import to_coupon_response
from src.domain.exceptions import InvalidCouponException


@dataclass
class ApplyCouponUseCase:
    coupon_repository: CouponRepositoryInterface

    async def execute(self, *, code: str, order_total: float) -> ApplyCouponResponse:
        normalized_code = code.strip().upper()
        coupon = await self.coupon_repository.get_by_code(normalized_code)
        if coupon is None:
            raise ResourceNotFoundException("Coupon", normalized_code)

        if not coupon.is_valid_at(datetime.now(UTC)):
            raise InvalidCouponException(normalized_code)

        discount_amount = coupon.calculate_discount(order_total)
        coupon.register_use()
        saved = await self.coupon_repository.save(coupon)

        return ApplyCouponResponse(
            coupon=to_coupon_response(saved),
            discount_amount=discount_amount,
            final_total=round(order_total - discount_amount, 2),
        )
