"""Fake em memória de `CouponRepositoryInterface` — usado pelos testes unitários."""

from __future__ import annotations

from src.domain.entities.coupon import Coupon


class FakeCouponStore:
    def __init__(self, coupons: list[Coupon] | None = None) -> None:
        self._coupons: dict[str, Coupon] = {c.code: c for c in (coupons or [])}

    async def get_by_code(self, code: str) -> Coupon | None:
        return self._coupons.get(code.strip().upper())

    async def list_all(self) -> list[Coupon]:
        return list(self._coupons.values())

    async def add(self, coupon: Coupon) -> Coupon:
        self._coupons[coupon.code] = coupon
        return coupon

    async def save(self, coupon: Coupon) -> Coupon:
        self._coupons[coupon.code] = coupon
        return coupon
