"""Testes do módulo de emissão e validação de tokens JWT."""

import time

import jwt as pyjwt
import pytest
from restaurant_security.jwt import create_access_token, create_refresh_token, decode_access_token

SECRET = "test-secret-key-32-chars-long-security"
USER_ID = "019124a3-4411-77bb-88cc-123456789abc"
TENANT_ID = "019124a1-7c2a-71b3-810a-3199d0c64921"
ROLE = "MANAGER"


def test_create_access_token_returns_string_with_expected_claims() -> None:
    token = create_access_token(
        user_id=USER_ID,
        tenant_id=TENANT_ID,
        role=ROLE,
        secret_key=SECRET,
        expires_delta_minutes=15,
    )

    assert isinstance(token, str)
    decoded = decode_access_token(token, SECRET)

    assert decoded["sub"] == USER_ID
    assert decoded["tenant_id"] == TENANT_ID
    assert decoded["role"] == ROLE
    assert "jti" in decoded


def test_each_token_has_a_unique_jti_for_revocation_control() -> None:
    first = decode_access_token(create_access_token(USER_ID, TENANT_ID, ROLE, SECRET), SECRET)
    second = decode_access_token(create_access_token(USER_ID, TENANT_ID, ROLE, SECRET), SECRET)

    assert first["jti"] != second["jti"]


def test_decode_access_token_rejects_wrong_secret() -> None:
    token = create_access_token(USER_ID, TENANT_ID, ROLE, SECRET)

    with pytest.raises(pyjwt.InvalidSignatureError):
        decode_access_token(token, "outra-chave-secreta-completamente-diferente")


def test_decode_access_token_rejects_expired_token() -> None:
    token = create_access_token(USER_ID, TENANT_ID, ROLE, SECRET, expires_delta_minutes=-1)
    time.sleep(0.01)

    with pytest.raises(pyjwt.ExpiredSignatureError):
        decode_access_token(token, SECRET)


def test_create_access_token_defaults_token_type_to_access() -> None:
    decoded = decode_access_token(create_access_token(USER_ID, TENANT_ID, ROLE, SECRET), SECRET)

    assert decoded["token_type"] == "access"


def test_create_refresh_token_is_marked_with_refresh_token_type() -> None:
    refresh_token = create_refresh_token(USER_ID, TENANT_ID, ROLE, SECRET, expires_delta_days=7)

    decoded = decode_access_token(refresh_token, SECRET)
    assert decoded["token_type"] == "refresh"


def test_create_refresh_token_expires_much_further_than_access_token() -> None:
    access_decoded = decode_access_token(
        create_access_token(USER_ID, TENANT_ID, ROLE, SECRET), SECRET
    )
    refresh_decoded = decode_access_token(
        create_refresh_token(USER_ID, TENANT_ID, ROLE, SECRET), SECRET
    )

    assert refresh_decoded["exp"] > access_decoded["exp"]
