"""Entidades de Domínio do Módulo de Autenticação e Identidade (DDD)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class UserRole(StrEnum):
    """Papéis RBAC do sistema (docs/SECURITY.md §3)."""

    SUPER_ADMIN = "SUPER_ADMIN"
    RESTAURANT_OWNER = "RESTAURANT_OWNER"
    MANAGER = "MANAGER"
    CASHIER = "CASHIER"
    WAITER = "WAITER"
    KITCHEN_STAFF = "KITCHEN_STAFF"
    CUSTOMER = "CUSTOMER"


# Papéis que podem autenticar via PIN de 4 dígitos no POS/App Garçom
# (login rápido, sem digitar e-mail/senha em um terminal compartilhado).
PIN_LOGIN_ELIGIBLE_ROLES = frozenset(
    {UserRole.WAITER, UserRole.CASHIER, UserRole.MANAGER, UserRole.KITCHEN_STAFF}
)


@dataclass
class User:
    """Entidade Raiz do Agregado de Usuário.

    Attributes:
        id: UUIDv7 do usuário.
        tenant_id: UUID do restaurante ao qual o usuário pertence.
        email: Endereço de e-mail único (por tenant).
        hashed_password: Hash Argon2id da senha (nunca a senha em texto claro).
        name: Nome completo do usuário/funcionário.
        role: Papel RBAC no sistema.
        pin_hash: Hash Argon2id do PIN de 4 dígitos, se elegível a login rápido.
        is_active: Indica se a conta pode autenticar.
    """

    id: uuid.UUID
    tenant_id: uuid.UUID
    email: str
    hashed_password: str
    name: str
    role: UserRole
    pin_hash: str | None = None
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def can_login_with_pin(self) -> bool:
        """Verifica se este usuário pode autenticar via PIN de 4 dígitos."""
        return (
            self.is_active and self.pin_hash is not None and self.role in PIN_LOGIN_ELIGIBLE_ROLES
        )

    def can_login_with_password(self) -> bool:
        """Verifica se este usuário pode autenticar via e-mail/senha."""
        return self.is_active
