"""Testes unitários dos casos de uso do `marketing-service` (repositório fake, sem DB real)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from restaurant_core.exceptions import ResourceNotFoundException
from src.application.use_cases.apply_coupon import ApplyCouponUseCase
from src.application.use_cases.create_coupon import CreateCouponUseCase, ListCouponsUseCase
from src.domain.entities.coupon import Coupon, DiscountType
from src.domain.exceptions import DuplicateCouponCodeException, InvalidCouponException
from tests.unit.fakes import FakeCouponStore

_NOW = datetime.now(UTC)


@pytest.mark.asyncio
async def test_create_coupon_persists_and_returns_response() -> None:
    tenant_id = uuid.uuid4()
    use_case = CreateCouponUseCase(coupon_repository=FakeCouponStore())

    response = await use_case.execute(
        tenant_id=tenant_id,
        code="promo10",
        discount_type=DiscountType.PERCENTAGE,
        discount_value=10.0,
        valid_from=_NOW - timedelta(days=1),
        valid_until=_NOW + timedelta(days=1),
        max_uses=None,
    )

    assert response.code == "PROMO10"


@pytest.mark.asyncio
async def test_create_coupon_rejects_duplicate_code() -> None:
    tenant_id = uuid.uuid4()
    store = FakeCouponStore(
        [
            Coupon(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                code="PROMO10",
                discount_type=DiscountType.PERCENTAGE,
                discount_value=10.0,
                valid_from=_NOW - timedelta(days=1),
                valid_until=_NOW + timedelta(days=1),
            )
        ]
    )
    use_case = CreateCouponUseCase(coupon_repository=store)

    with pytest.raises(DuplicateCouponCodeException):
        await use_case.execute(
            tenant_id=tenant_id,
            code="promo10",
            discount_type=DiscountType.FIXED,
            discount_value=5.0,
            valid_from=_NOW - timedelta(days=1),
            valid_until=_NOW + timedelta(days=1),
            max_uses=None,
        )


@pytest.mark.asyncio
async def test_list_coupons_returns_all() -> None:
    store = FakeCouponStore(
        [
            Coupon(
                id=uuid.uuid4(),
                tenant_id=uuid.uuid4(),
                code="A",
                discount_type=DiscountType.FIXED,
                discount_value=5.0,
                valid_from=_NOW - timedelta(days=1),
                valid_until=_NOW + timedelta(days=1),
            )
        ]
    )
    use_case = ListCouponsUseCase(coupon_repository=store)

    result = await use_case.execute()

    assert len(result) == 1


@pytest.mark.asyncio
async def test_apply_coupon_computes_discount_and_final_total() -> None:
    coupon = Coupon(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        code="PROMO10",
        discount_type=DiscountType.PERCENTAGE,
        discount_value=10.0,
        valid_from=_NOW - timedelta(days=1),
        valid_until=_NOW + timedelta(days=1),
    )
    use_case = ApplyCouponUseCase(coupon_repository=FakeCouponStore([coupon]))

    response = await use_case.execute(code="promo10", order_total=100.0)

    assert response.discount_amount == 10.0
    assert response.final_total == 90.0
    assert response.coupon.times_used == 1


@pytest.mark.asyncio
async def test_apply_coupon_not_found_raises() -> None:
    use_case = ApplyCouponUseCase(coupon_repository=FakeCouponStore())
    with pytest.raises(ResourceNotFoundException):
        await use_case.execute(code="NOPE", order_total=50.0)


@pytest.mark.asyncio
async def test_apply_coupon_expired_raises_invalid_coupon() -> None:
    coupon = Coupon(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        code="EXPIRED",
        discount_type=DiscountType.FIXED,
        discount_value=5.0,
        valid_from=_NOW - timedelta(days=10),
        valid_until=_NOW - timedelta(days=1),
    )
    use_case = ApplyCouponUseCase(coupon_repository=FakeCouponStore([coupon]))

    with pytest.raises(InvalidCouponException):
        await use_case.execute(code="EXPIRED", order_total=50.0)
