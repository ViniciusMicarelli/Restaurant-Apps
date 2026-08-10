"""Testes do `SQLAlchemyRepository` genérico: escopo de tenant e lock otimista."""

import uuid

import pytest
from restaurant_core.exceptions import OptimisticLockException, ResourceNotFoundException
from restaurant_database.repository import SQLAlchemyRepository
from sqlalchemy.ext.asyncio import AsyncSession


def _widget_repository(
    session: AsyncSession, tenant_id: uuid.UUID, model: type
) -> SQLAlchemyRepository:
    """Cria uma instância de repositório concreto para `model`, sem mutar estado compartilhado entre testes."""
    repository_class = type(
        f"{model.__name__}Repository", (SQLAlchemyRepository,), {"model": model}
    )
    return repository_class(session, tenant_id)


@pytest.mark.asyncio
async def test_add_and_get_by_id_returns_the_created_entity(
    sqlite_session: AsyncSession, sample_widget_model
) -> None:
    tenant_id = uuid.uuid4()
    repo = _widget_repository(sqlite_session, tenant_id, sample_widget_model)

    created = await repo.add_model(sample_widget_model(tenant_id=tenant_id, name="Mesa 1"))
    await sqlite_session.commit()

    fetched = await repo.get_model_by_id(created.id)
    assert fetched is not None
    assert fetched.name == "Mesa 1"


@pytest.mark.asyncio
async def test_get_by_id_never_leaks_data_across_tenants(
    sqlite_session: AsyncSession, sample_widget_model
) -> None:
    tenant_a, tenant_b = uuid.uuid4(), uuid.uuid4()
    repo_a = _widget_repository(sqlite_session, tenant_a, sample_widget_model)
    repo_b = _widget_repository(sqlite_session, tenant_b, sample_widget_model)

    created = await repo_a.add_model(
        sample_widget_model(tenant_id=tenant_a, name="Segredo do Tenant A")
    )
    await sqlite_session.commit()

    assert await repo_b.get_model_by_id(created.id) is None
    assert await repo_a.get_model_by_id(created.id) is not None


@pytest.mark.asyncio
async def test_get_by_id_or_raise_raises_resource_not_found(
    sqlite_session: AsyncSession, sample_widget_model
) -> None:
    repo = _widget_repository(sqlite_session, uuid.uuid4(), sample_widget_model)

    with pytest.raises(ResourceNotFoundException):
        await repo.get_model_by_id_or_raise(uuid.uuid4(), "SampleWidget")


@pytest.mark.asyncio
async def test_soft_delete_excludes_entity_from_subsequent_reads(
    sqlite_session: AsyncSession, sample_widget_model
) -> None:
    tenant_id = uuid.uuid4()
    repo = _widget_repository(sqlite_session, tenant_id, sample_widget_model)

    created = await repo.add_model(sample_widget_model(tenant_id=tenant_id, name="Mesa a remover"))
    await sqlite_session.commit()

    await repo.soft_delete_model(created)
    await sqlite_session.commit()

    assert await repo.get_model_by_id(created.id) is None


@pytest.mark.asyncio
async def test_save_raises_optimistic_lock_exception_on_stale_write(
    sqlite_session: AsyncSession, sample_widget_model
) -> None:
    tenant_id = uuid.uuid4()
    repo = _widget_repository(sqlite_session, tenant_id, sample_widget_model)

    created = await repo.add_model(sample_widget_model(tenant_id=tenant_id, name="Original"))
    await sqlite_session.commit()

    # Simula uma escrita concorrente: outra transação já avançou a version_id no banco.
    await sqlite_session.execute(
        sample_widget_model.__table__.update()
        .where(sample_widget_model.__table__.c.id == created.id)
        .values(version_id=created.version_id + 1)
    )
    await sqlite_session.commit()

    created.name = "Alterado por uma sessão desatualizada"
    with pytest.raises(OptimisticLockException):
        await repo.save_model(created)
