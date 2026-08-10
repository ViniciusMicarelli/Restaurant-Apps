"""Contexto assíncrono de Multi-Tenancy (ADR-003: Row-Level Isolation).

Fornece o `ContextVar` que carrega o `tenant_id` da requisição corrente e o
`TenantContextMiddleware` que o popula a partir do JWT (ou, para rotas
públicas pré-autenticação como o cardápio digital via QR Code, do header
`X-Tenant-Id`). Repositórios (`restaurant_database`) leem este contexto para
injetar `WHERE tenant_id = :current_tenant_id` automaticamente em toda query.
"""

from __future__ import annotations

import uuid
from contextvars import ContextVar, Token

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from restaurant_security.jwt import decode_access_token

_current_tenant_id: ContextVar[uuid.UUID | None] = ContextVar("current_tenant_id", default=None)


def get_current_tenant_id_or_none() -> uuid.UUID | None:
    """Retorna o `tenant_id` da requisição corrente, ou `None` se não definido."""
    return _current_tenant_id.get()


def set_current_tenant_id(tenant_id: uuid.UUID) -> Token[uuid.UUID | None]:
    """Define manualmente o tenant corrente (uso em workers/scripts fora de requisições HTTP)."""
    return _current_tenant_id.set(tenant_id)


def reset_current_tenant_id(token: Token[uuid.UUID | None]) -> None:
    """Restaura o valor anterior do contexto de tenant."""
    _current_tenant_id.reset(token)


class TenantContextMiddleware(BaseHTTPMiddleware):
    """Middleware ASGI que extrai o `tenant_id` e o disponibiliza via `ContextVar`.

    Ordem de resolução:
    1. Claim `tenant_id` de um Bearer JWT válido no header `Authorization`.
    2. Header `X-Tenant-Id` explícito (usado por rotas públicas pré-login,
       ex: cardápio digital do `customer-web` acessado via QR Code).

    Se nenhuma das duas fontes estiver presente, o contexto permanece `None`
    e endpoints que dependem de tenant scoping devem falhar explicitamente
    via a dependency `require_tenant_id` (nunca operar sem filtro).
    """

    def __init__(self, app: object, jwt_secret_key: str) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self._jwt_secret_key = jwt_secret_key

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        tenant_id = self._resolve_tenant_id(request)
        token = _current_tenant_id.set(tenant_id)
        try:
            return await call_next(request)
        finally:
            _current_tenant_id.reset(token)

    def _resolve_tenant_id(self, request: Request) -> uuid.UUID | None:
        authorization = request.headers.get("authorization", "")
        if authorization.startswith("Bearer "):
            raw_token = authorization.removeprefix("Bearer ").strip()
            try:
                claims = decode_access_token(raw_token, self._jwt_secret_key)
                return uuid.UUID(str(claims["tenant_id"]))
            except Exception:
                pass

        header_tenant_id = request.headers.get("x-tenant-id")
        if header_tenant_id:
            try:
                return uuid.UUID(header_tenant_id)
            except ValueError:
                return None

        return None
