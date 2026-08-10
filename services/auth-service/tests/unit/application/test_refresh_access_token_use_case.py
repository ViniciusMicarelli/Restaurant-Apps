"""Testes unitários de `RefreshAccessTokenUseCase`."""

import uuid
from typing import Any

import pytest
from restaurant_security.jwt import create_access_token, create_refresh_token
from src.application.use_cases.refresh_access_token import RefreshAccessTokenUseCase
from src.domain.entities.user import User, UserRole
from src.domain.exceptions import InvalidCredentialsError, TokenRevokedError
from tests.unit.fakes import FakeTokenBlacklist, FakeUserStore

SECRET = "test-secret-key-32-chars-long-security"


def _make_user(**overrides: Any) -> User:
    defaults: dict[str, Any] = {
        "id": uuid.uuid4(),
        "tenant_id": uuid.uuid4(),
        "email": "gerente@burgerhouse.com.br",
        "hashed_password": "hashed",
        "name": "Gerente",
        "role": UserRole.MANAGER,
    }
    defaults.update(overrides)
    return User(**defaults)


def _use_case(store: FakeUserStore, blacklist: FakeTokenBlacklist) -> RefreshAccessTokenUseCase:
    return RefreshAccessTokenUseCase(
        user_lookup=store,
        token_blacklist=blacklist,
        jwt_secret_key=SECRET,
        access_token_expire_minutes=15,
        refresh_token_expire_days=7,
    )


@pytest.mark.asyncio
async def test_refresh_with_valid_token_returns_new_pair_and_revokes_the_old_one() -> None:
    user = _make_user()
    store = FakeUserStore([user])
    blacklist = FakeTokenBlacklist()
    refresh_token = create_refresh_token(str(user.id), str(user.tenant_id), user.role.value, SECRET)

    response = await _use_case(store, blacklist).execute(refresh_token=refresh_token)

    assert response.access_token
    assert response.refresh_token != refresh_token
    assert len(blacklist.blacklisted) == 1


@pytest.mark.asyncio
async def test_refresh_rejects_an_access_token_used_as_refresh_token() -> None:
    user = _make_user()
    store = FakeUserStore([user])
    access_token = create_access_token(str(user.id), str(user.tenant_id), user.role.value, SECRET)

    with pytest.raises(InvalidCredentialsError):
        await _use_case(store, FakeTokenBlacklist()).execute(refresh_token=access_token)


@pytest.mark.asyncio
async def test_refresh_rejects_a_blacklisted_refresh_token() -> None:
    user = _make_user()
    store = FakeUserStore([user])
    blacklist = FakeTokenBlacklist()
    refresh_token = create_refresh_token(str(user.id), str(user.tenant_id), user.role.value, SECRET)

    # Primeira renovação: consome (blacklista) o refresh token original.
    await _use_case(store, blacklist).execute(refresh_token=refresh_token)

    # Reutilizar o MESMO refresh token uma segunda vez deve falhar.
    with pytest.raises(TokenRevokedError):
        await _use_case(store, blacklist).execute(refresh_token=refresh_token)


@pytest.mark.asyncio
async def test_refresh_rejects_token_for_a_user_that_no_longer_exists() -> None:
    store = FakeUserStore()  # nenhum usuário cadastrado
    refresh_token = create_refresh_token(str(uuid.uuid4()), str(uuid.uuid4()), "MANAGER", SECRET)

    with pytest.raises(InvalidCredentialsError):
        await _use_case(store, FakeTokenBlacklist()).execute(refresh_token=refresh_token)


@pytest.mark.asyncio
async def test_refresh_rejects_malformed_token() -> None:
    with pytest.raises(InvalidCredentialsError):
        await _use_case(FakeUserStore(), FakeTokenBlacklist()).execute(refresh_token="not-a-jwt")
