"""Caso de uso: renovação do access token a partir de um refresh token válido.

Aplica rotação de refresh token (docs/SECURITY.md): o refresh token usado é
imediatamente revogado (blacklist do `jti`) e um novo par é emitido — um
refresh token nunca pode ser reutilizado duas vezes.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

import jwt as pyjwt
from src.application.dtos.user_dtos import TokenResponse
from src.application.interfaces.repository_interface import (
    TokenBlacklistInterface,
    UserLookupInterface,
)
from src.application.use_cases._shared import issue_token_pair
from src.domain.exceptions import InvalidCredentialsError, TokenRevokedError


@dataclass
class RefreshAccessTokenUseCase:
    """Valida um refresh token, o revoga e emite um novo par access/refresh."""

    user_lookup: UserLookupInterface
    token_blacklist: TokenBlacklistInterface
    jwt_secret_key: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int

    async def execute(self, *, refresh_token: str) -> TokenResponse:
        try:
            claims = pyjwt.decode(refresh_token, self.jwt_secret_key, algorithms=["HS256"])
        except pyjwt.InvalidTokenError as exc:
            raise InvalidCredentialsError("Refresh token inválido ou expirado.") from exc

        if claims.get("token_type") != "refresh":
            raise InvalidCredentialsError("Token informado não é um refresh token válido.")

        jti = str(claims["jti"])
        if await self.token_blacklist.is_blacklisted(jti):
            raise TokenRevokedError()

        user = await self.user_lookup.find_by_id(uuid.UUID(str(claims["sub"])))
        if user is None or not user.can_login_with_password():
            raise InvalidCredentialsError("Usuário inexistente ou inativo.")

        ttl_seconds = max(int(claims["exp"]) - int(claims["iat"]), 0)
        await self.token_blacklist.blacklist(jti, ttl_seconds)

        return issue_token_pair(
            user,
            jwt_secret_key=self.jwt_secret_key,
            access_token_expire_minutes=self.access_token_expire_minutes,
            refresh_token_expire_days=self.refresh_token_expire_days,
        )
