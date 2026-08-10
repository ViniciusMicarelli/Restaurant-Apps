"""DTOs (Pydantic v2) de Request/Response do serviço de Autenticação.

Todo DTO de escrita usa `extra="forbid"` (docs/SECURITY.md §2.5 — proteção
contra Mass Assignment): o cliente nunca consegue injetar campos como
`role` ou `tenant_id` além do que cada endpoint explicitamente aceita.

Há DOIS caminhos de cadastro deliberadamente distintos:
- `RegisterOwnerRequest`: único endpoint não-autenticado do serviço, usado
  uma única vez logo após o `restaurant-service` criar um novo tenant, para
  cadastrar seu primeiro usuário (o dono). Aceita `tenant_id` explícito
  porque, nesse instante, ainda não existe ninguém autenticado nesse tenant.
- `RegisterEmployeeRequest`: protegido por `require_role(OWNER, MANAGER)`;
  NUNCA aceita `tenant_id` do cliente — o `tenant_id` usado é sempre o do
  usuário autenticado (extraído do JWT), impedindo que um gerente crie
  funcionários em um tenant alheio (IDOR).
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from src.domain.entities.user import UserRole

# Papéis que um endpoint autenticado de "cadastrar funcionário" pode atribuir.
# SUPER_ADMIN e RESTAURANT_OWNER ficam de fora deliberadamente (nenhuma
# escalação de privilégio via este endpoint).
ASSIGNABLE_EMPLOYEE_ROLES = (
    UserRole.MANAGER,
    UserRole.CASHIER,
    UserRole.WAITER,
    UserRole.KITCHEN_STAFF,
)


class RegisterOwnerRequest(BaseModel):
    """Payload do cadastro (único, não-autenticado) do dono de um tenant novo."""

    model_config = ConfigDict(extra="forbid")

    tenant_id: uuid.UUID = Field(
        ..., description="ID do restaurante, criado previamente pelo restaurant-service"
    )
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    name: str = Field(..., min_length=2, max_length=150)


class RegisterEmployeeRequest(BaseModel):
    """Payload de cadastro de funcionário por um Owner/Manager já autenticado."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    name: str = Field(..., min_length=2, max_length=150)
    role: UserRole = Field(default=UserRole.WAITER)
    pin: str | None = Field(default=None, min_length=4, max_length=4, pattern=r"^\d{4}$")

    @field_validator("role")
    @classmethod
    def _role_must_be_assignable(cls, role: UserRole) -> UserRole:
        """Bloqueia escalação de privilégio: nunca aceita SUPER_ADMIN/RESTAURANT_OWNER aqui."""
        if role not in ASSIGNABLE_EMPLOYEE_ROLES:
            raise ValueError(
                f"Papel '{role.value}' não pode ser atribuído por este endpoint "
                f"(permitidos: {', '.join(r.value for r in ASSIGNABLE_EMPLOYEE_ROLES)})."
            )
        return role


class RegisterUserResponse(BaseModel):
    """Resposta de cadastro — nunca inclui hash de senha/PIN."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    email: str
    name: str
    role: UserRole


class LoginWithPasswordRequest(BaseModel):
    """Payload de login tradicional com e-mail e senha."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(..., min_length=1)


class LoginWithPinRequest(BaseModel):
    """Payload de login rápido para Garçom/Caixa/Cozinha via PIN de 4 dígitos."""

    model_config = ConfigDict(extra="forbid")

    tenant_id: uuid.UUID
    pin: str = Field(..., min_length=4, max_length=4, pattern=r"^\d{4}$")


class RefreshTokenRequest(BaseModel):
    """Payload de renovação de access token a partir de um refresh token válido."""

    model_config = ConfigDict(extra="forbid")

    refresh_token: str


class UserProfileResponse(BaseModel):
    """Perfil público do usuário autenticado, devolvido em login/`/me`."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    email: str
    name: str
    role: UserRole


class TokenResponse(BaseModel):
    """Resposta contendo o par de tokens JWT e o perfil do usuário autenticado."""

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in_seconds: int
    user: UserProfileResponse
