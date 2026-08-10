"""Fixtures dos testes de integração do `menu-service` (SQLite + índice de busca fake)."""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator, Generator

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("PORT", "8002")
os.environ.setdefault("JWT_SECRET_KEY", "integration-test-secret-key-32chars")
os.environ.setdefault("DB__HOST", "unused")
os.environ.setdefault("DB__PORT", "5432")
os.environ.setdefault("DB__USER", "unused")
os.environ.setdefault("DB__PASSWORD", "unused")
os.environ.setdefault("DB__NAME", "unused")
os.environ.setdefault("REDIS__HOST", "unused")
os.environ.setdefault("REDIS__PORT", "6379")
os.environ.setdefault("REDIS__DB", "0")
os.environ.setdefault(
    "MEILISEARCH_URL", "http://127.0.0.1:1"
)  # porta inválida = connection refused instantâneo, sem DNS
os.environ.setdefault("MEILISEARCH_MASTER_KEY", "unused")

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from restaurant_database.base import BaseDBModel
from restaurant_security.rate_limiter import InMemoryRateLimiter
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from src.presentation.api.v1 import dependencies as deps
from tests.unit.fakes import FakeSearchIndex


@pytest_asyncio.fixture
async def sqlite_session_factory() -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(BaseDBModel.metadata.create_all)

    yield async_sessionmaker(bind=engine, expire_on_commit=False)

    await engine.dispose()


@pytest.fixture
def rate_limiter() -> InMemoryRateLimiter:
    return InMemoryRateLimiter()


@pytest.fixture
def client(
    sqlite_session_factory: async_sessionmaker[AsyncSession],
    rate_limiter: InMemoryRateLimiter,
) -> Generator[TestClient, None, None]:
    from src.main import app  # noqa: PLC0415

    async def override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
        async with sqlite_session_factory() as session:
            yield session

    fake_search_index = FakeSearchIndex()

    app.dependency_overrides[deps.get_db_session] = override_get_db_session
    app.dependency_overrides[deps.get_search_index] = lambda: fake_search_index
    app.dependency_overrides[deps.get_rate_limiter] = lambda: rate_limiter

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
