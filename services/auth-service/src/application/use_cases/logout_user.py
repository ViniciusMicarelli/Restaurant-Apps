"""Caso de uso: logout — revoga o `jti` do access token corrente até sua expiração natural."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from src.application.interfaces.repository_interface import TokenBlacklistInterface


@dataclass
class LogoutUserUseCase:
    """Adiciona o `jti` do token corrente à blacklist pelo tempo restante de validade."""

    token_blacklist: TokenBlacklistInterface

    async def execute(self, *, jti: str, expires_at: datetime) -> None:
        ttl_seconds = max(int((expires_at - datetime.now(UTC)).total_seconds()), 0)
        await self.token_blacklist.blacklist(jti, ttl_seconds)
