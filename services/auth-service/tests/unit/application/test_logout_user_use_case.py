"""Testes unitários de `LogoutUserUseCase`."""

from datetime import UTC, datetime, timedelta

import pytest
from src.application.use_cases.logout_user import LogoutUserUseCase
from tests.unit.fakes import FakeTokenBlacklist


@pytest.mark.asyncio
async def test_logout_blacklists_the_jti_with_positive_ttl() -> None:
    blacklist = FakeTokenBlacklist()
    use_case = LogoutUserUseCase(token_blacklist=blacklist)

    await use_case.execute(jti="jti-123", expires_at=datetime.now(UTC) + timedelta(minutes=10))

    assert await blacklist.is_blacklisted("jti-123") is True
    assert blacklist.blacklisted["jti-123"] > 0


@pytest.mark.asyncio
async def test_logout_with_already_expired_token_uses_zero_ttl_without_raising() -> None:
    blacklist = FakeTokenBlacklist()
    use_case = LogoutUserUseCase(token_blacklist=blacklist)

    await use_case.execute(jti="jti-expired", expires_at=datetime.now(UTC) - timedelta(minutes=10))

    assert blacklist.blacklisted["jti-expired"] == 0
