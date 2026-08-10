"""Contratos de repositório do serviço de Marketing."""

from __future__ import annotations

from typing import Protocol

from src.domain.entities.coupon import Coupon


class CouponRepositoryInterface(Protocol):
    async def get_by_code(self, code: str) -> Coupon | None: ...

    async def list_all(self) -> list[Coupon]: ...

    async def add(self, coupon: Coupon) -> Coupon: ...

    async def save(self, coupon: Coupon) -> Coupon: ...
