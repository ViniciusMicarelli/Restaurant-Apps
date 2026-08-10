"""Testes da entidade de domínio `Coupon`."""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from src.domain.entities.coupon import Coupon, DiscountType

_NOW = datetime(2026, 8, 5, 12, 0, tzinfo=UTC)


def _make_coupon(**overrides: Any) -> Coupon:
    defaults: dict[str, Any] = {
        "id": uuid.uuid4(),
        "tenant_id": uuid.uuid4(),
        "code": "promo10",
        "discount_type": DiscountType.PERCENTAGE,
        "discount_value": 10.0,
        "valid_from": _NOW - timedelta(days=1),
        "valid_until": _NOW + timedelta(days=1),
    }
    defaults.update(overrides)
    return Coupon(**defaults)


def test_code_is_normalized_to_uppercase() -> None:
    coupon = _make_coupon(code="promo10")
    assert coupon.code == "PROMO10"


def test_rejects_empty_code() -> None:
    with pytest.raises(ValueError, match="código"):
        _make_coupon(code="   ")


def test_rejects_percentage_discount_above_100() -> None:
    with pytest.raises(ValueError, match="100%"):
        _make_coupon(discount_type=DiscountType.PERCENTAGE, discount_value=150.0)


def test_rejects_valid_until_before_valid_from() -> None:
    with pytest.raises(ValueError, match="posterior"):
        _make_coupon(valid_from=_NOW, valid_until=_NOW - timedelta(days=1))


def test_rejects_max_uses_below_one() -> None:
    with pytest.raises(ValueError, match="ao menos 1"):
        _make_coupon(max_uses=0)


def test_is_valid_at_within_window() -> None:
    coupon = _make_coupon()
    assert coupon.is_valid_at(_NOW) is True


def test_is_valid_at_outside_window() -> None:
    coupon = _make_coupon()
    assert coupon.is_valid_at(_NOW + timedelta(days=10)) is False


def test_is_valid_at_inactive() -> None:
    coupon = _make_coupon(active=False)
    assert coupon.is_valid_at(_NOW) is False


def test_is_valid_at_max_uses_reached() -> None:
    coupon = _make_coupon(max_uses=1, times_used=1)
    assert coupon.is_valid_at(_NOW) is False


def test_calculate_discount_percentage() -> None:
    coupon = _make_coupon(discount_type=DiscountType.PERCENTAGE, discount_value=10.0)
    assert coupon.calculate_discount(200.0) == 20.0


def test_calculate_discount_fixed() -> None:
    coupon = _make_coupon(discount_type=DiscountType.FIXED, discount_value=15.0)
    assert coupon.calculate_discount(200.0) == 15.0


def test_calculate_discount_fixed_never_exceeds_total() -> None:
    coupon = _make_coupon(discount_type=DiscountType.FIXED, discount_value=500.0)
    assert coupon.calculate_discount(50.0) == 50.0


def test_register_use_increments_counter() -> None:
    coupon = _make_coupon()
    coupon.register_use()
    assert coupon.times_used == 1
