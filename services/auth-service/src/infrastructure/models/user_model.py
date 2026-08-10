"""Modelo SQLAlchemy 2.0 da tabela `users` no PostgreSQL isolado (`auth_db`)."""

from __future__ import annotations

from restaurant_database import TenantAwareModel
from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column
from src.domain.entities.user import UserRole


class UserModel(TenantAwareModel):
    """Mapeamento da tabela `users` — herda `id`/`tenant_id`/auditoria/lock otimista.

    E-mail é único GLOBALMENTE (não só por tenant), de propósito: o login por
    e-mail/senha (`POST /auth/login`) não conhece o `tenant_id` de antemão —
    é precisamente esse lookup que o resolve. Ver `SQLAlchemyUserLookupRepository`
    para a única consulta do serviço que legitimamente não filtra por tenant.
    """

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), nullable=False, default=UserRole.CUSTOMER
    )
    pin_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
