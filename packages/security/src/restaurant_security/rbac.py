"""Dependencies FastAPI para Autenticação, RBAC e escopo de Tenant.

Todo endpoint que manipula dados de um restaurante deve declarar
`tenant_id: Annotated[UUID, Depends(require_tenant_id)]` (ou depender de
`get_current_user`, que já resolve o tenant a partir do JWT). Rotas que
exigem um papel específico usam `Depends(require_role(get_current_user, "MANAGER", ...))`.

NOTA: este módulo NÃO usa `from __future__ import annotations`. O FastAPI
precisa avaliar a anotação `Annotated[CurrentUser, Depends(get_current_user)]`
em `require_role` para extrair o `Depends(...)` — como `get_current_user` é
uma variável local (closure) de `require_role`/`build_get_current_user`, e
não um nome do módulo, a avaliação tardia (postponed evaluation) de
anotações não consegue resolvê-la, fazendo o FastAPI tratar o parâmetro como
query param em vez de sub-dependency. Mantendo as anotações avaliadas
imediatamente (comportamento padrão sem o `__future__` import), o objeto
`Depends(...)` real já está presente no momento da definição da função.
"""

import uuid
from collections.abc import Callable, Coroutine
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import Depends, Header
from restaurant_core.exceptions import (
    ForbiddenException,
    TenantIsolationException,
    UnauthorizedException,
)

from restaurant_security.jwt import decode_access_token
from restaurant_security.tenant_context import get_current_tenant_id_or_none

# Papéis padrão do RBAC/ABAC (docs/SECURITY.md §3).
SUPER_ADMIN = "SUPER_ADMIN"
RESTAURANT_OWNER = "RESTAURANT_OWNER"
MANAGER = "MANAGER"
CASHIER = "CASHIER"
WAITER = "WAITER"
KITCHEN_STAFF = "KITCHEN_STAFF"
CUSTOMER = "CUSTOMER"


class CurrentUser:
    """Representação tipada do usuário autenticado extraído do JWT."""

    __slots__ = ("expires_at", "jti", "role", "tenant_id", "user_id")

    def __init__(
        self, user_id: uuid.UUID, tenant_id: uuid.UUID, role: str, jti: str, expires_at: datetime
    ) -> None:
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.role = role
        self.jti = jti
        self.expires_at = expires_at


def build_get_current_user(jwt_secret_key: str) -> Callable[..., Coroutine[Any, Any, CurrentUser]]:
    """Fábrica da dependency `get_current_user`, ligada ao segredo JWT do serviço."""

    async def get_current_user(
        authorization: Annotated[str | None, Header()] = None,
    ) -> CurrentUser:
        if not authorization or not authorization.startswith("Bearer "):
            raise UnauthorizedException("Header de Autorização Bearer ausente ou mal formatado.")

        raw_token = authorization.removeprefix("Bearer ").strip()
        try:
            claims = decode_access_token(raw_token, jwt_secret_key)
        except Exception as exc:
            raise UnauthorizedException("Token JWT inválido ou expirado.") from exc

        if claims.get("token_type", "access") != "access":
            raise UnauthorizedException(
                "Um refresh token não pode ser usado para autenticar requisições."
            )

        return CurrentUser(
            user_id=uuid.UUID(str(claims["sub"])),
            tenant_id=uuid.UUID(str(claims["tenant_id"])),
            role=str(claims["role"]),
            jti=str(claims["jti"]),
            expires_at=datetime.fromtimestamp(int(claims["exp"]), tz=UTC),
        )

    return get_current_user


def require_role(
    get_current_user: Callable[..., Coroutine[Any, Any, CurrentUser]], *allowed_roles: str
) -> Callable[..., Coroutine[Any, Any, CurrentUser]]:
    """Dependency factory que garante que o usuário autenticado possua um dos papéis permitidos.

    Recebe explicitamente a dependency `get_current_user` (obtida via
    `build_get_current_user`) porque o FastAPI precisa dela declarada com
    `Depends(...)` no parâmetro interno para resolver o usuário antes de
    checar o papel — não é possível injetá-la implicitamente.
    """

    async def _dependency(
        current_user: Annotated[CurrentUser, Depends(get_current_user)],
    ) -> CurrentUser:
        if current_user.role not in allowed_roles:
            raise ForbiddenException(
                f"Papel '{current_user.role}' não possui permissão para esta operação "
                f"(requer um de: {', '.join(allowed_roles)})."
            )
        return current_user

    return _dependency


def require_tenant_id() -> uuid.UUID:
    """Dependency que exige um `tenant_id` resolvido pelo `TenantContextMiddleware`.

    Usada em rotas públicas (ex: cardápio digital) que não passam por
    `get_current_user`, mas ainda assim precisam de escopo de tenant.
    """
    tenant_id = get_current_tenant_id_or_none()
    if tenant_id is None:
        raise TenantIsolationException()
    return tenant_id


__all__ = [
    "CASHIER",
    "CUSTOMER",
    "KITCHEN_STAFF",
    "MANAGER",
    "RESTAURANT_OWNER",
    "SUPER_ADMIN",
    "WAITER",
    "CurrentUser",
    "build_get_current_user",
    "require_role",
    "require_tenant_id",
]
