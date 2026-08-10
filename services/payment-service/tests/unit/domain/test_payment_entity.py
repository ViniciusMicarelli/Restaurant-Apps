"""Testes das entidades de domínio `Payment`/`PaymentSplit`."""

import uuid

import pytest
from src.domain.entities.payment import Payment, PaymentSplit
from src.domain.entities.payment_method import PaymentMethod


def _make_payment(splits: list[PaymentSplit]) -> Payment:
    return Payment(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        order_id=uuid.uuid4(),
        cash_register_id=uuid.uuid4(),
        splits=splits,
    )


def test_payment_split_rejects_non_positive_amount() -> None:
    with pytest.raises(ValueError, match="positivo"):
        PaymentSplit(payment_method=PaymentMethod.CASH, amount=0)


def test_payment_requires_at_least_one_split() -> None:
    with pytest.raises(ValueError, match="ao menos uma parcela"):
        _make_payment([])


def test_total_amount_sums_all_splits() -> None:
    payment = _make_payment(
        [
            PaymentSplit(payment_method=PaymentMethod.PIX, amount=30.0),
            PaymentSplit(payment_method=PaymentMethod.CASH, amount=20.0),
        ]
    )
    assert payment.total_amount == 50.0


def test_cash_amount_sums_only_cash_splits() -> None:
    payment = _make_payment(
        [
            PaymentSplit(payment_method=PaymentMethod.PIX, amount=30.0),
            PaymentSplit(payment_method=PaymentMethod.CASH, amount=20.0),
            PaymentSplit(payment_method=PaymentMethod.CASH, amount=5.0),
        ]
    )
    assert payment.cash_amount == 25.0


def test_assert_splits_match_expected_total_passes_within_tolerance() -> None:
    payment = _make_payment([PaymentSplit(payment_method=PaymentMethod.PIX, amount=50.0)])
    payment.assert_splits_match_expected_total(50.001)  # dentro da tolerância de 1 centavo


def test_assert_splits_match_expected_total_raises_when_mismatched() -> None:
    payment = _make_payment([PaymentSplit(payment_method=PaymentMethod.PIX, amount=50.0)])
    with pytest.raises(ValueError, match="não corresponde ao"):
        payment.assert_splits_match_expected_total(60.0)
