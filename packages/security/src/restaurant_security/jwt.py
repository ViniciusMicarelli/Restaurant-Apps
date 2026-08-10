"""Módulo de Emissão, Assinatura e Validação de Tokens JWT.

Utiliza algoritmos modernos de criptografia para autenticação stateless
e controle de sessão com suporte a rotação e revogação via JTI (JWT ID).
"""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from pydantic import BaseModel, Field

# Algoritmo de assinatura padrão recomendado
JWT_ALGORITHM = "HS256"


class TokenPayload(BaseModel):
    """Estrutura Pydantic v2 contendo os claims internos do token JWT."""

    sub: str = Field(..., description="ID do Usuário (UUIDv7)")
    tenant_id: str = Field(..., description="ID do Restaurante / Tenant ID")
    role: str = Field(..., description="Cargo do usuário no sistema (ex: MANAGER, WAITER)")
    jti: str = Field(..., description="JWT ID único para controle de revogação/blacklist")
    token_type: str = Field(default="access", description="'access' ou 'refresh'")
    exp: datetime = Field(..., description="Data/hora de expiração do token")
    iat: datetime = Field(..., description="Data/hora de emissão do token")


def create_access_token(  # noqa: PLR0913 - 6 parâmetros nomeados são mais claros que agrupar em um DTO aqui
    user_id: str,
    tenant_id: str,
    role: str,
    secret_key: str,
    *,
    expires_delta_minutes: int = 15,
    token_type: str = "access",
) -> str:
    """Gera um Token JWT assinado (access ou refresh, conforme `token_type`).

    Args:
        user_id: UUID do usuário autenticado.
        tenant_id: UUID do restaurante/tenant.
        role: Papel/Cargo do usuário (RBAC).
        secret_key: Chave secreta de assinatura.
        expires_delta_minutes: Minutos para expiração (default: 15min).
        token_type: `"access"` (padrão) ou `"refresh"` — permite que quem
            decodifica rejeite um refresh token usado como access token.

    Returns:
        String codificada e assinada do JWT.
    """
    now = datetime.now(UTC)
    expiration = now + timedelta(minutes=expires_delta_minutes)

    payload = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "role": str(role),
        "jti": str(uuid.uuid4()),
        "token_type": token_type,
        "exp": int(expiration.timestamp()),
        "iat": int(now.timestamp()),
    }

    return jwt.encode(payload, secret_key, algorithm=JWT_ALGORITHM)


def create_refresh_token(
    user_id: str,
    tenant_id: str,
    role: str,
    secret_key: str,
    expires_delta_days: int = 7,
) -> str:
    """Gera um Refresh Token JWT de longa duração (`token_type="refresh"`)."""
    return create_access_token(
        user_id=user_id,
        tenant_id=tenant_id,
        role=role,
        secret_key=secret_key,
        expires_delta_minutes=expires_delta_days * 24 * 60,
        token_type="refresh",
    )


def decode_access_token(token: str, secret_key: str) -> dict[str, Any]:
    """Decodifica e valida a assinatura e expiração do Token JWT.

    Args:
        token: String codificada do Token JWT.
        secret_key: Chave secreta de verificação.

    Returns:
        Dicionário contendo os claims do token.

    Raises:
        jwt.ExpiredSignatureError: Se o token tiver expirado.
        jwt.InvalidTokenError: Se o token for inválido ou adulterado.
    """
    return jwt.decode(token, secret_key, algorithms=[JWT_ALGORITHM])
