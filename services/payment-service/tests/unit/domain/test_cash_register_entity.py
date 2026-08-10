"""Testes da entidade de domínio `CashRegister`."""

import uuid
from typing import Any

import pytest
from src.domain.entities.cash_register import CashRegister, CashRegisterStatus


def _make_register(**overrides: Any) -> CashRegister:
    defaults: dict[str, Any] = {
        "id": uuid.uuid4(),
        "tenant_id": uuid.uuid4(),
        "operator_id": uuid.uuid4(),
        "opening_amount": 150.0,
        "current_balance": 150.0,
    }
    defaults.update(overrides)
    return CashRegister(**defaults)


def test_register_rejects_negative_opening_amount() -> None:
    with pytest.raises(ValueError, match="negativo"):
        _make_register(opening_amount=-1.0, current_balance=-1.0)


def test_register_sets_opened_at_automatically() -> None:
    register = _make_register()
    assert register.opened_at is not None


def test_apply_cash_movement_increases_balance() -> None:
    register = _make_register(current_balance=150.0)
    register.apply_cash_movement(50.0)
    assert register.current_balance == 200.0


def test_apply_cash_movement_decreases_balance() -> None:
    register = _make_register(current_balance=150.0)
    register.apply_cash_movement(-50.0)
    assert register.current_balance == 100.0


def test_apply_cash_movement_rejects_resulting_negative_balance() -> None:
    register = _make_register(current_balance=50.0)
    with pytest.raises(ValueError, match="saldo negativo"):
        register.apply_cash_movement(-100.0)


def test_apply_cash_movement_rejects_closed_register() -> None:
    register = _make_register(status=CashRegisterStatus.CLOSED)
    with pytest.raises(ValueError, match="fechado"):
        register.apply_cash_movement(10.0)


def test_close_computes_positive_divergence() -> None:
    register = _make_register(current_balance=200.0)
    register.close(210.0)
    assert register.status == CashRegisterStatus.CLOSED
    assert register.closing_counted_amount == 210.0
    assert register.closing_divergence == 10.0
    assert register.closed_at is not None


def test_close_computes_negative_divergence() -> None:
    register = _make_register(current_balance=200.0)
    register.close(180.0)
    assert register.closing_divergence == -20.0


def test_close_already_closed_register_raises() -> None:
    register = _make_register(status=CashRegisterStatus.CLOSED)
    with pytest.raises(ValueError, match="já está fechado"):
        register.close(100.0)


def test_close_rejects_negative_counted_amount() -> None:
    register = _make_register()
    with pytest.raises(ValueError, match="negativo"):
        register.close(-5.0)
