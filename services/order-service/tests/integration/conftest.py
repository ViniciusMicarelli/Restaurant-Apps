"""Fixtures dos testes de integração do `order-service` (SQLite + EventBus/Idempotency em memória)."""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator, Generator

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("PORT", "8005")
os.environ.setdefault("JWT_SECRET_KEY", "integration-test-secret-key-32chars")
os.environ.setdefault("DB__HOST", "unused")
os.environ.setdefault("DB__PORT", "5432")
os.environ.setdefault("DB__USER", "unused")
os.environ.setdefault("DB__PASSWORD", "unused")
os.environ.setdefault("DB__NAME", "unused")
os.environ.setdefault("REDIS__HOST", "unused")
os.environ.setdefault("REDIS__PORT", "6379")
os.environ.setdefault("REDIS__DB", "0")
# 127.0.0.1 com porta fechada = connection refused quase instantâneo, ao
# contrário de um hostname inexistente (que sofre timeout de resolução DNS).
os.environ.setdefault("RABBITMQ__HOST", "127.0.0.1")
os.environ.setdefault("RABBITMQ__PORT", "1")
os.environ.setdefault("RABBITMQ__USER", "unused")
os.environ.setdefault("RABBITMQ__PASSWORD", "unused")

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from restaurant_database.base import BaseDBModel
from restaurant_events import InMemoryEventBus
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from src.infrastructure.cache.idempotency_store import InMemoryIdempotencyStore
from src.presentation.api.v1 import dependencies as deps


@pytest_asyncio.fixture
async def sqlite_session_factory() -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(BaseDBModel.metadata.create_all)

    yield async_sessionmaker(bind=engine, expire_on_commit=False)

    await engine.dispose()


@pytest.fixture
def event_bus() -> InMemoryEventBus:
    return InMemoryEventBus()


@pytest.fixture
def client(
    sqlite_session_factory: async_sessionmaker[AsyncSession], event_bus: InMemoryEventBus
) -> Generator[TestClient, None, None]:
    from src.main import app  # noqa: PLC0415

    async def override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
        async with sqlite_session_factory() as session:
            yield session

    idempotency_store = InMemoryIdempotencyStore()

    app.dependency_overrides[deps.get_db_session] = override_get_db_session
    app.dependency_overrides[deps.get_event_bus] = lambda: event_bus
    app.dependency_overrides[deps.get_idempotency_store] = lambda: idempotency_store

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
