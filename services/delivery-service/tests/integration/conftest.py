"""Fixtures dos testes de integração do `delivery-service` (SQLite)."""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator, Generator

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("PORT", "8008")
os.environ.setdefault("JWT_SECRET_KEY", "integration-test-secret-key-32chars")
os.environ.setdefault("DB__HOST", "unused")
os.environ.setdefault("DB__PORT", "5432")
os.environ.setdefault("DB__USER", "unused")
os.environ.setdefault("DB__PASSWORD", "unused")
os.environ.setdefault("DB__NAME", "unused")

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from restaurant_database.base import BaseDBModel
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from src.presentation.api.v1 import dependencies as deps


@pytest_asyncio.fixture
async def sqlite_session_factory() -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(BaseDBModel.metadata.create_all)

    yield async_sessionmaker(bind=engine, expire_on_commit=False)

    await engine.dispose()


@pytest.fixture
def client(
    sqlite_session_factory: async_sessionmaker[AsyncSession],
) -> Generator[TestClient, None, None]:
    from src.main import app  # noqa: PLC0415

    async def override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
        async with sqlite_session_factory() as session:
            yield session

    app.dependency_overrides[deps.get_db_session] = override_get_db_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
