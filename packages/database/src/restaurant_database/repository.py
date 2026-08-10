"""Repositório base genérico com escopo automático de Tenant e Lock Otimista.

Implementa o padrão "Repository Pattern com Interfaces" (docs/ai/patterns.md):
os repositórios concretos de cada microsserviço (`infrastructure/repositories/
sqlalchemy_repository.py`) devem estender `SQLAlchemyRepository[Model]` para
herdar CRUD tenant-scoped, em vez de reescrever `WHERE tenant_id = ...` em
cada consulta manualmente.

Os métodos aqui operam no nível do MODELO ORM (`ModelT`) e usam o prefixo
`*_model`/`*_models` deliberadamente — as interfaces de domínio de cada
serviço (`application/interfaces/repository_interface.py`) expõem métodos
como `get_by_id`/`list_all`/`add` que retornam ENTIDADES DE DOMÍNIO, não
`ModelT`. Se os repositórios concretos reaproveitassem esses mesmos nomes
via `override`, o retorno mudaria de tipo (`ModelT` → entidade de domínio),
o que o mypy (corretamente) rejeita como violação de LSP. Repositórios
concretos devem chamar `super().get_model_by_id(...)` etc. internamente e
expor seus PRÓPRIOS métodos (`get_by_id`, `list_all`, ...) fazendo a
tradução ORM → domínio, sem colidir de nome com a classe base.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from restaurant_core.exceptions import OptimisticLockException, ResourceNotFoundException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.exc import StaleDataError

from restaurant_database.base import TenantAwareModel


class SQLAlchemyRepository[ModelT: TenantAwareModel]:
    """Repositório base tenant-aware para um modelo SQLAlchemy específico.

    NUNCA remove os filtros automáticos de `tenant_id` (ADR-003) — toda
    consulta feita por este repositório já inclui `tenant_id = :current`.
    """

    model: type[ModelT]

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    async def get_model_by_id(self, entity_id: uuid.UUID) -> ModelT | None:
        """Busca o modelo ORM pelo ID, escopado ao tenant corrente e não removido."""
        stmt = select(self.model).where(
            self.model.id == entity_id,
            self.model.tenant_id == self._tenant_id,
            self.model.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_model_by_id_or_raise(self, entity_id: uuid.UUID, resource_name: str) -> ModelT:
        """Busca o modelo ORM pelo ID ou lança `ResourceNotFoundException`."""
        entity = await self.get_model_by_id(entity_id)
        if entity is None:
            raise ResourceNotFoundException(resource_name, str(entity_id))
        return entity

    async def list_models(self, *, limit: int = 50, offset: int = 0) -> list[ModelT]:
        """Lista modelos ORM ativos do tenant corrente, paginados."""
        stmt = (
            select(self.model)
            .where(self.model.tenant_id == self._tenant_id, self.model.deleted_at.is_(None))
            .order_by(self.model.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def add_model(self, entity: ModelT) -> ModelT:
        """Registra um novo modelo ORM na sessão corrente (flush imediato para obter o ID gerado)."""
        self._session.add(entity)
        await self._session.flush()
        return entity

    async def save_model(self, entity: ModelT) -> ModelT:
        """Persiste alterações em um modelo ORM já rastreado, detectando conflitos de Lock Otimista."""
        try:
            await self._session.flush()
        except StaleDataError as exc:
            raise OptimisticLockException(self.model.__name__) from exc
        return entity

    async def soft_delete_model(self, entity: ModelT) -> None:
        """Marca o modelo ORM como removido (soft delete) preservando o histórico para auditoria."""
        entity.deleted_at = datetime.now(UTC)
        await self.save_model(entity)
