"""Testes unitários de `LoginWithPasswordUseCase`."""

import uuid

import pytest
from restaurant_security.hash import hash_password
from src.application.use_cases.login_with_password import LoginWithPasswordUseCase
from src.domain.entities.user import User, UserRole
from src.domain.exceptions import InvalidCredentialsError
from tests.unit.fakes import FakeUserStore

SECRET = "test-secret-key-32-chars-long-security"


def _use_case(store: FakeUserStore) -> LoginWithPasswordUseCase:
    return LoginWithPasswordUseCase(
        user_lookup=store,
        jwt_secret_key=SECRET,
        access_token_expire_minutes=15,
        refresh_token_expire_days=7,
    )


@pytest.mark.asyncio
async def test_login_with_correct_password_returns_token_pair() -> None:
    tenant_id = uuid.uuid4()
    user = User(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        email="gerente@burgerhouse.com.br",
        hashed_password=hash_password("SenhaForte@123"),
        name="Gerente",
        role=UserRole.MANAGER,
    )
    store = FakeUserStore([user])

    response = await _use_case(store).execute(
        email="gerente@burgerhouse.com.br", password="SenhaForte@123"
    )

    assert response.user.tenant_id == tenant_id
    assert response.access_token
    assert response.refresh_token
    assert response.access_token != response.refresh_token


@pytest.mark.asyncio
async def test_login_with_wrong_password_raises_invalid_credentials() -> None:
    user = User(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        email="gerente@burgerhouse.com.br",
        hashed_password=hash_password("SenhaForte@123"),
        name="Gerente",
        role=UserRole.MANAGER,
    )
    store = FakeUserStore([user])

    with pytest.raises(InvalidCredentialsError):
        await _use_case(store).execute(email="gerente@burgerhouse.com.br", password="SenhaErrada")


@pytest.mark.asyncio
async def test_login_with_unknown_email_raises_invalid_credentials_not_not_found() -> None:
    """Não deve vazar se o e-mail existe (proteção contra enumeração — docs/SECURITY.md)."""
    store = FakeUserStore()

    with pytest.raises(InvalidCredentialsError):
        await _use_case(store).execute(email="ninguem@burgerhouse.com.br", password="qualquer")


@pytest.mark.asyncio
async def test_login_rejects_inactive_user() -> None:
    user = User(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        email="demitido@burgerhouse.com.br",
        hashed_password=hash_password("SenhaForte@123"),
        name="Ex-funcionário",
        role=UserRole.WAITER,
        is_active=False,
    )
    store = FakeUserStore([user])

    with pytest.raises(InvalidCredentialsError):
        await _use_case(store).execute(
            email="demitido@burgerhouse.com.br", password="SenhaForte@123"
        )
