"""Caso de uso: login rápido por PIN de 4 dígitos (Garçom/Caixa/Cozinha)."""

from __future__ import annotations

from dataclasses import dataclass

from restaurant_security.hash import verify_pin
from src.application.dtos.user_dtos import TokenResponse
from src.application.interfaces.repository_interface import UserRepositoryInterface
from src.application.use_cases._shared import issue_token_pair
from src.domain.exceptions import InvalidCredentialsError


@dataclass
class LoginWithPinUseCase:
    """Autentica um usuário por PIN dentro de um tenant e emite o par de tokens JWT.

    Como o PIN é hasheado com salt aleatório (Argon2id), não é possível fazer
    um `SELECT ... WHERE pin_hash = ...` direto — a verificação percorre os
    usuários ativos elegíveis do tenant (tipicamente dezenas, não milhões).
    """

    user_repository: UserRepositoryInterface
    jwt_secret_key: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int

    async def execute(self, *, pin: str) -> TokenResponse:
        candidates = await self.user_repository.list_pin_eligible_active_users()
        matched_user = next(
            (u for u in candidates if u.pin_hash and verify_pin(pin, u.pin_hash)), None
        )

        if matched_user is None:
            raise InvalidCredentialsError("PIN inválido para este restaurante.")

        return issue_token_pair(
            matched_user,
            jwt_secret_key=self.jwt_secret_key,
            access_token_expire_minutes=self.access_token_expire_minutes,
            refresh_token_expire_days=self.refresh_token_expire_days,
        )
