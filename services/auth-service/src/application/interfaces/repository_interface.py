"""Contrato do repositório de usuários (Repository Pattern com Interfaces).

A camada `application` depende apenas deste `Protocol`; a implementação
concreta (`infrastructure/repositories/sqlalchemy_user_repository.py`) é
injetada em runtime — nenhum caso de uso importa SQLAlchemy diretamente.
"""

from __future__ import annotations

import uuid
from typing import Protocol

from src.domain.entities.user import User


class UserRepositoryInterface(Protocol):
    """Operações de persistência tenant-scoped necessárias pelos casos de uso de Auth."""

    async def get_by_id(self, user_id: uuid.UUID) -> User | None: ...

    async def list_pin_eligible_active_users(self) -> list[User]:
        """Lista usuários ativos elegíveis a login por PIN no tenant corrente."""
        ...

    async def add(self, user: User) -> User: ...


class UserLookupInterface(Protocol):
    """Buscas de `User` SEM escopo de tenant — apenas para os 2 casos legítimos:

    1. `find_by_email`: login por e-mail/senha e checagem de duplicidade no
       cadastro (e-mail é único globalmente — `UserModel.email` — não por
       tenant), quando o `tenant_id` ainda não é conhecido.
    2. `find_by_id`: renovação de access token a partir de um refresh token
       JÁ VALIDADO criptograficamente (assinatura conferida) — o `user_id`
       (UUID) é globalmente único, e o `tenant_id` embutido no JWT não pode
       ter sido forjado, então usar esse lookup aqui é seguro.

    Nenhum outro caso de uso deve depender desta interface nem usá-la para
    operações de escrita.
    """

    async def find_by_email(self, email: str) -> User | None: ...

    async def find_by_id(self, user_id: uuid.UUID) -> User | None: ...


class TokenBlacklistInterface(Protocol):
    """Contrato do armazenamento de revogação de tokens (Redis em produção)."""

    async def blacklist(self, jti: str, ttl_seconds: int) -> None: ...

    async def is_blacklisted(self, jti: str) -> bool: ...


class RateLimiterInterface(Protocol):
    """Contrato de throttle de tentativas por chave (Redis em produção) —
    usado para limitar força bruta em `/login`/`/login-pin` (docs/SECURITY.md §2.7)."""

    async def hit(self, key: str, *, max_attempts: int, window_seconds: int) -> bool: ...
