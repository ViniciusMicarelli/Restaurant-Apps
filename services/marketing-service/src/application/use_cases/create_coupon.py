"""Casos de uso: criação e listagem de cupons de desconto."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from restaurant_core.ids import generate_uuid7
from src.application.dtos.marketing_dtos import CouponResponse
from src.application.interfaces.repository_interface import CouponRepositoryInterface
from src.application.use_cases._shared import to_coupon_response
from src.domain.entities.coupon import Coupon, DiscountType
from src.domain.exceptions import DuplicateCouponCodeException


@dataclass
class CreateCouponUseCase:
    coupon_repository: CouponRepositoryInterface

    async def execute(  # noqa: PLR0913 - parâmetros nomeados (keyword-only) mapeando 1:1 com o DTO de entrada
        self,
        *,
        tenant_id: uuid.UUID,
        code: str,
        discount_type: DiscountType,
        discount_value: float,
        valid_from: datetime,
        valid_until: datetime,
        max_uses: int | None,
    ) -> CouponResponse:
        existing = await self.coupon_repository.get_by_code(code.strip().upper())
        if existing is not None:
            raise DuplicateCouponCodeException(code)

        coupon = Coupon(
            id=generate_uuid7(),
            tenant_id=tenant_id,
            code=code,
            discount_type=discount_type,
            discount_value=discount_value,
            valid_from=valid_from,
            valid_until=valid_until,
            max_uses=max_uses,
        )
        created = await self.coupon_repository.add(coupon)
        return to_coupon_response(created)


@dataclass
class ListCouponsUseCase:
    coupon_repository: CouponRepositoryInterface

    async def execute(self) -> list[CouponResponse]:
        coupons = await self.coupon_repository.list_all()
        return [to_coupon_response(c) for c in coupons]
