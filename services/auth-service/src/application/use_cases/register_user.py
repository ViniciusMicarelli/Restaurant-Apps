"""Caso de uso: cadastro de um novo usuário (dono, na criação do tenant, ou
funcionário, quando executado por um Owner/Manager autenticado)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from restaurant_core.ids import generate_uuid7
from restaurant_security.hash import hash_password, hash_pin
from src.application.dtos.user_dtos import RegisterUserResponse
from src.application.interfaces.repository_interface import (
    UserLookupInterface,
    UserRepositoryInterface,
)
from src.domain.entities.user import User, UserRole
from src.domain.exceptions import DuplicateEmailError


@dataclass
class RegisterUserUseCase:
    """Persiste um novo `User` com senha (e, opcionalmente, PIN) já hasheados.

    O `tenant_id` é sempre resolvido pela camada de apresentação (nunca
    aceito cru do corpo de uma requisição autenticada) — ver `user_dtos.py`.
    """

    user_repository: UserRepositoryInterface
    user_lookup: UserLookupInterface

    async def execute(  # noqa: PLR0913 - 6 parâmetros nomeados (keyword-only) são mais claros que um DTO aqui
        self,
        *,
        tenant_id: uuid.UUID,
        email: str,
        password: str,
        name: str,
        role: UserRole,
        pin: str | None = None,
    ) -> RegisterUserResponse:
        if await self.user_lookup.find_by_email(email) is not None:
            raise DuplicateEmailError(email)

        user = User(
            id=generate_uuid7(),
            tenant_id=tenant_id,
            email=email,
            hashed_password=hash_password(password),
            name=name,
            role=role,
            pin_hash=hash_pin(pin) if pin else None,
        )
        created = await self.user_repository.add(user)

        return RegisterUserResponse(
            id=created.id,
            tenant_id=created.tenant_id,
            email=created.email,
            name=created.name,
            role=created.role,
        )
