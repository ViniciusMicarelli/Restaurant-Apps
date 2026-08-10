"""Caso de uso: login tradicional com e-mail e senha."""

from __future__ import annotations

from dataclasses import dataclass

from restaurant_security.hash import verify_password
from src.application.dtos.user_dtos import TokenResponse
from src.application.interfaces.repository_interface import UserLookupInterface
from src.application.use_cases._shared import issue_token_pair
from src.domain.exceptions import InvalidCredentialsError


@dataclass
class LoginWithPasswordUseCase:
    """Autentica um usuário por e-mail/senha (busca global, ver `UserLookupInterface`)
    e emite o par de tokens JWT já com o `tenant_id` resolvido."""

    user_lookup: UserLookupInterface
    jwt_secret_key: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int

    async def execute(self, *, email: str, password: str) -> TokenResponse:
        user = await self.user_lookup.find_by_email(email)

        # Mensagem genérica em ambos os casos (usuário inexistente vs senha
        # errada) — evita enumeração de e-mails cadastrados (docs/SECURITY.md).
        if user is None or not user.can_login_with_password():
            raise InvalidCredentialsError("E-mail ou senha inválidos.")
        if not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError("E-mail ou senha inválidos.")

        return issue_token_pair(
            user,
            jwt_secret_key=self.jwt_secret_key,
            access_token_expire_minutes=self.access_token_expire_minutes,
            refresh_token_expire_days=self.refresh_token_expire_days,
        )
