"""Helper interno compartilhado pelos casos de uso de login (password/PIN).

Não é um caso de uso em si (sem `execute()`), por isso o prefixo `_` — evita
duplicar a emissão do par access/refresh token nos dois fluxos de login.
"""

from __future__ import annotations

from restaurant_security.jwt import create_access_token, create_refresh_token
from src.application.dtos.user_dtos import TokenResponse, UserProfileResponse
from src.domain.entities.user import User


def issue_token_pair(
    user: User,
    *,
    jwt_secret_key: str,
    access_token_expire_minutes: int,
    refresh_token_expire_days: int,
) -> TokenResponse:
    """Emite o par de tokens JWT (access + refresh) para um usuário já autenticado."""
    access_token = create_access_token(
        user_id=str(user.id),
        tenant_id=str(user.tenant_id),
        role=user.role.value,
        secret_key=jwt_secret_key,
        expires_delta_minutes=access_token_expire_minutes,
    )
    refresh_token = create_refresh_token(
        user_id=str(user.id),
        tenant_id=str(user.tenant_id),
        role=user.role.value,
        secret_key=jwt_secret_key,
        expires_delta_days=refresh_token_expire_days,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in_seconds=access_token_expire_minutes * 60,
        user=UserProfileResponse(
            id=user.id, tenant_id=user.tenant_id, email=user.email, name=user.name, role=user.role
        ),
    )
