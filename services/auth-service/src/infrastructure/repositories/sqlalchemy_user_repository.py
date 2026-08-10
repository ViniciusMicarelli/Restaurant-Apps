"""Implementações concretas dos repositórios de usuário sobre SQLAlchemy 2.0 Async."""

from __future__ import annotations

import uuid

from restaurant_database import SQLAlchemyRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.entities.user import PIN_LOGIN_ELIGIBLE_ROLES, User
from src.infrastructure.models.user_model import UserModel


def _to_entity(model: UserModel) -> User:
    return User(
        id=model.id,
        tenant_id=model.tenant_id,
        email=model.email,
        hashed_password=model.hashed_password,
        name=model.name,
        role=model.role,
        pin_hash=model.pin_hash,
        is_active=model.is_active,
        created_at=model.created_at,
    )


class SQLAlchemyUserRepository(SQLAlchemyRepository[UserModel]):
    """Repositório tenant-aware de `User` — todas as consultas escopadas ao tenant do construtor."""

    model = UserModel

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        model = await super().get_model_by_id(user_id)
        return _to_entity(model) if model is not None else None

    async def list_pin_eligible_active_users(self) -> list[User]:
        stmt = select(UserModel).where(
            UserModel.tenant_id == self._tenant_id,
            UserModel.deleted_at.is_(None),
            UserModel.is_active.is_(True),
            UserModel.pin_hash.is_not(None),
            UserModel.role.in_(list(PIN_LOGIN_ELIGIBLE_ROLES)),
        )
        result = await self._session.execute(stmt)
        return [_to_entity(model) for model in result.scalars().all()]

    async def add(self, user: User) -> User:
        model = UserModel(
            id=user.id,
            tenant_id=user.tenant_id,
            email=user.email,
            hashed_password=user.hashed_password,
            name=user.name,
            role=user.role,
            pin_hash=user.pin_hash,
            is_active=user.is_active,
        )
        created = await super().add_model(model)
        return _to_entity(created)


class SQLAlchemyUserLookupRepository:
    """Implementa `UserLookupInterface` — a ÚNICA consulta do serviço sem filtro de tenant.

    Usada pelo login por e-mail/senha e pela checagem de duplicidade no
    cadastro, ambos os casos em que o `tenant_id` ainda não é conhecido.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_email(self, email: str) -> User | None:
        stmt = select(UserModel).where(UserModel.email == email, UserModel.deleted_at.is_(None))
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def find_by_id(self, user_id: uuid.UUID) -> User | None:
        stmt = select(UserModel).where(UserModel.id == user_id, UserModel.deleted_at.is_(None))
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return _to_entity(model) if model is not None else None
