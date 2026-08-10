"""Fakes em memória das interfaces de `application/interfaces` — usados pelos
testes unitários de caso de uso (nunca tocam banco de dados real).

`FakeUserStore` implementa tanto `UserRepositoryInterface` (tenant-scoped)
quanto `UserLookupInterface` (global) sobre o MESMO dicionário em memória —
assim um usuário criado via `add()` já aparece para `find_by_email()`, como
aconteceria com um banco real compartilhando a mesma tabela.
"""

from __future__ import annotations

import uuid

from src.domain.entities.user import User


class FakeUserStore:
    """Store em memória compartilhado, usado como `user_repository` e/ou `user_lookup`."""

    def __init__(self, users: list[User] | None = None) -> None:
        self._users: dict[uuid.UUID, User] = {u.id: u for u in (users or [])}

    def scoped_to(self, tenant_id: uuid.UUID) -> FakeUserRepository:
        """Retorna uma "view" tenant-scoped deste mesmo store (mesmo dict subjacente)."""
        return FakeUserRepository(self._users, tenant_id)

    # --- UserLookupInterface (global, sem tenant) ---------------------------

    async def find_by_email(self, email: str) -> User | None:
        return next((u for u in self._users.values() if u.email == email), None)

    async def find_by_id(self, user_id: uuid.UUID) -> User | None:
        return self._users.get(user_id)


class FakeUserRepository:
    """Implementação em memória de `UserRepositoryInterface`, escopada a um tenant."""

    def __init__(self, users: dict[uuid.UUID, User], tenant_id: uuid.UUID) -> None:
        self._users = users
        self.tenant_id = tenant_id

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        user = self._users.get(user_id)
        return user if user and user.tenant_id == self.tenant_id else None

    async def list_pin_eligible_active_users(self) -> list[User]:
        return [
            u
            for u in self._users.values()
            if u.tenant_id == self.tenant_id and u.can_login_with_pin()
        ]

    async def add(self, user: User) -> User:
        self._users[user.id] = user
        return user


class FakeTokenBlacklist:
    """Implementação em memória de `TokenBlacklistInterface`."""

    def __init__(self) -> None:
        self.blacklisted: dict[str, int] = {}

    async def blacklist(self, jti: str, ttl_seconds: int) -> None:
        self.blacklisted[jti] = ttl_seconds

    async def is_blacklisted(self, jti: str) -> bool:
        return jti in self.blacklisted
