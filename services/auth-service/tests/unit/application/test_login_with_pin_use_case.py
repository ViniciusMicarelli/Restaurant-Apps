"""Testes unitários de `LoginWithPinUseCase`."""

import uuid

import pytest
from restaurant_security.hash import hash_pin
from src.application.use_cases.login_with_pin import LoginWithPinUseCase
from src.domain.entities.user import User, UserRole
from src.domain.exceptions import InvalidCredentialsError
from tests.unit.fakes import FakeUserStore

SECRET = "test-secret-key-32-chars-long-security"


def _use_case(store: FakeUserStore, tenant_id: uuid.UUID) -> LoginWithPinUseCase:
    return LoginWithPinUseCase(
        user_repository=store.scoped_to(tenant_id),
        jwt_secret_key=SECRET,
        access_token_expire_minutes=15,
        refresh_token_expire_days=7,
    )


@pytest.mark.asyncio
async def test_login_with_correct_pin_returns_token_for_the_matching_user() -> None:
    tenant_id = uuid.uuid4()
    waiter = User(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        email="joao@burgerhouse.com.br",
        hashed_password="unused",
        name="Garçom João",
        role=UserRole.WAITER,
        pin_hash=hash_pin("1234"),
    )
    store = FakeUserStore([waiter])

    response = await _use_case(store, tenant_id).execute(pin="1234")

    assert response.user.email == "joao@burgerhouse.com.br"


@pytest.mark.asyncio
async def test_login_with_pin_never_matches_a_user_from_another_tenant() -> None:
    tenant_a, tenant_b = uuid.uuid4(), uuid.uuid4()
    waiter_in_tenant_a = User(
        id=uuid.uuid4(),
        tenant_id=tenant_a,
        email="joao@burgerhouse.com.br",
        hashed_password="unused",
        name="Garçom João",
        role=UserRole.WAITER,
        pin_hash=hash_pin("1234"),
    )
    store = FakeUserStore([waiter_in_tenant_a])

    with pytest.raises(InvalidCredentialsError):
        await _use_case(store, tenant_b).execute(pin="1234")


@pytest.mark.asyncio
async def test_login_with_wrong_pin_raises_invalid_credentials() -> None:
    tenant_id = uuid.uuid4()
    waiter = User(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        email="joao@burgerhouse.com.br",
        hashed_password="unused",
        name="Garçom João",
        role=UserRole.WAITER,
        pin_hash=hash_pin("1234"),
    )
    store = FakeUserStore([waiter])

    with pytest.raises(InvalidCredentialsError):
        await _use_case(store, tenant_id).execute(pin="9999")


@pytest.mark.asyncio
async def test_customer_role_is_never_a_pin_login_candidate_even_with_matching_pin() -> None:
    tenant_id = uuid.uuid4()
    customer = User(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        email="cliente@example.com",
        hashed_password="unused",
        name="Cliente",
        role=UserRole.CUSTOMER,
        pin_hash=hash_pin("1234"),
    )
    store = FakeUserStore([customer])

    with pytest.raises(InvalidCredentialsError):
        await _use_case(store, tenant_id).execute(pin="1234")
