"""Testes da entidade de domínio `User`."""

import uuid
from typing import Any

from src.domain.entities.user import User, UserRole


def _make_user(**overrides: Any) -> User:
    defaults: dict[str, Any] = {
        "id": uuid.uuid4(),
        "tenant_id": uuid.uuid4(),
        "email": "waiter@burgerhouse.com.br",
        "hashed_password": "hashed",
        "name": "Garçom João",
        "role": UserRole.WAITER,
        "pin_hash": "hashed-pin",
        "is_active": True,
    }
    defaults.update(overrides)
    return User(**defaults)


def test_waiter_with_pin_hash_can_login_with_pin() -> None:
    assert _make_user(role=UserRole.WAITER, pin_hash="x").can_login_with_pin() is True


def test_customer_role_cannot_login_with_pin_even_with_hash_set() -> None:
    assert _make_user(role=UserRole.CUSTOMER, pin_hash="x").can_login_with_pin() is False


def test_user_without_pin_hash_cannot_login_with_pin() -> None:
    assert _make_user(role=UserRole.WAITER, pin_hash=None).can_login_with_pin() is False


def test_inactive_user_cannot_login_with_pin_even_if_eligible() -> None:
    assert (
        _make_user(role=UserRole.MANAGER, pin_hash="x", is_active=False).can_login_with_pin()
        is False
    )


def test_active_user_can_login_with_password() -> None:
    assert _make_user(is_active=True).can_login_with_password() is True


def test_inactive_user_cannot_login_with_password() -> None:
    assert _make_user(is_active=False).can_login_with_password() is False
