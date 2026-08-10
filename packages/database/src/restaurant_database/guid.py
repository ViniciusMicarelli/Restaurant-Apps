"""Tipo de coluna UUID agnóstico de dialeto SQL.

Em PostgreSQL (produção/integration tests) usa o tipo nativo `UUID`.
Em outros dialetos (ex: SQLite em memória, usado pelos testes unitários de
repositório para não depender de um Postgres real de pé) grava como
`CHAR(32)` hexadecimal. Recipe padrão da documentação do SQLAlchemy.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.engine import Dialect
from sqlalchemy.types import CHAR, TypeDecorator


class GUID(TypeDecorator[uuid.UUID]):
    """Coluna UUID portável entre PostgreSQL e outros dialetos SQL."""

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect: Dialect) -> Any:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value: uuid.UUID | str | None, dialect: Dialect) -> str | None:
        if value is None:
            return None
        as_uuid = value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
        if dialect.name == "postgresql":
            return str(as_uuid)
        return as_uuid.hex

    def process_result_value(self, value: str | None, dialect: Dialect) -> uuid.UUID | None:
        if value is None:
            return None
        return value if isinstance(value, uuid.UUID) else uuid.UUID(value)
