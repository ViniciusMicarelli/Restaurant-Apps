"""Pacote de segurança: hashing Argon2id, JWT, contexto de tenant e RBAC."""

from restaurant_security.hash import hash_password, hash_pin, verify_password, verify_pin
from restaurant_security.jwt import (
    TokenPayload,
    create_access_token,
    create_refresh_token,
    decode_access_token,
)
from restaurant_security.rate_limiter import (
    InMemoryRateLimiter,
    RedisRateLimiter,
    resolve_rate_limit_key,
)
from restaurant_security.rbac import (
    CASHIER,
    CUSTOMER,
    KITCHEN_STAFF,
    MANAGER,
    RESTAURANT_OWNER,
    SUPER_ADMIN,
    WAITER,
    CurrentUser,
    build_get_current_user,
    require_role,
    require_tenant_id,
)
from restaurant_security.tenant_context import (
    TenantContextMiddleware,
    get_current_tenant_id_or_none,
    reset_current_tenant_id,
    set_current_tenant_id,
)

__all__ = [
    "CASHIER",
    "CUSTOMER",
    "KITCHEN_STAFF",
    "MANAGER",
    "RESTAURANT_OWNER",
    "SUPER_ADMIN",
    "WAITER",
    "CurrentUser",
    "InMemoryRateLimiter",
    "RedisRateLimiter",
    "TenantContextMiddleware",
    "TokenPayload",
    "build_get_current_user",
    "create_access_token",
    "create_refresh_token",
    "decode_access_token",
    "get_current_tenant_id_or_none",
    "hash_password",
    "hash_pin",
    "require_role",
    "require_tenant_id",
    "reset_current_tenant_id",
    "resolve_rate_limit_key",
    "set_current_tenant_id",
    "verify_password",
    "verify_pin",
]
