"""Caso de uso: obtém o perfil do usuário autenticado (`GET /api/v1/auth/me`)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from restaurant_core.exceptions import ResourceNotFoundException
from src.application.dtos.user_dtos import UserProfileResponse
from src.application.interfaces.repository_interface import UserRepositoryInterface


@dataclass
class GetUserProfileUseCase:
    """Busca o perfil público de um usuário pelo ID (já validado via JWT)."""

    user_repository: UserRepositoryInterface

    async def execute(self, *, user_id: uuid.UUID) -> UserProfileResponse:
        user = await self.user_repository.get_by_id(user_id)
        if user is None:
            raise ResourceNotFoundException("User", str(user_id))

        return UserProfileResponse(
            id=user.id, tenant_id=user.tenant_id, email=user.email, name=user.name, role=user.role
        )
