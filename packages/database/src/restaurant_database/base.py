"""Módulo de Classes Base de Entidades e Mixins do ORM SQLAlchemy 2.0.

Fornece a infraestrutura comum de persistência relacional com suporte a:
- Chaves primárias baseadas em UUIDv7.
- Isolamento automático de Multi-tenancy (coluna tenant_id).
- Audit trail automático (created_at, updated_at, deleted_at para soft delete).
- Lock Otimista via coluna version_id.
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from restaurant_core.ids import generate_uuid7
from sqlalchemy import DateTime, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from restaurant_database.guid import GUID


class BaseDBModel(DeclarativeBase):
    """Classe base declarativa abstrata para todas as tabelas do PostgreSQL."""

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=generate_uuid7,
        comment="Identificador único universal (UUIDv7)",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        comment="Data e hora de criação do registro (UTC)",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
        comment="Data e hora da última atualização do registro (UTC)",
    )

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        comment="Data de remoção lógica (Soft Delete). Se nulo, o registro está ativo.",
    )

    version_id: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="Versão do registro para controle de concorrência com Lock Otimista",
    )

    # `DeclarativeBase.__mapper_args__` é tipado como atributo de instância nos stubs do
    # SQLAlchemy; o padrão declarativo do ORM exige que seja definido como dict de classe
    # aqui, então a checagem `misc`/RUF012 do mypy/ruff para este caso específico é um falso
    # positivo conhecido da integração SQLAlchemy 2.0 + type checkers estritos.
    __mapper_args__: dict[str, Any] = {"version_id_col": version_id}  # noqa: RUF012


class TenantAwareModel(BaseDBModel):
    """Classe base abstrata para entidades dependentes de Multi-Tenancy.

    Todas as tabelas operacionais que pertencem a um restaurante específico
    devem herdar desta classe para garantir o isolamento estrito de tenant.
    """

    __abstract__ = True

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        nullable=False,
        index=True,
        comment="Identificador do restaurante proprietário do registro (Multi-Tenancy Tenant ID)",
    )
