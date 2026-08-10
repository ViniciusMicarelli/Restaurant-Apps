"""Fixtures dos testes de integração do `auth-service`.

Roda o app FastAPI real (router + use cases + repositórios SQLAlchemy) contra
um banco SQLite em memória (via `restaurant_database.GUID`, agnóstico de
dialeto) e uma blacklist de tokens em memória — sem exigir Postgres/Redis
reais de pé. Testes de integração contra um Postgres real (Docker) ficam
fora do escopo desta suíte "sempre-verde" (ver docs/testing/test_strategy.md).
"""

from __future__ import annotations

import os
import uuid
from collections.abc import AsyncGenerator, Generator

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("PORT", "8000")
os.environ.setdefault("JWT_SECRET_KEY", "integration-test-secret-key-32chars")
os.environ.setdefault("DB__HOST", "unused")
os.environ.setdefault("DB__PORT", "5432")
os.environ.setdefault("DB__USER", "unused")
os.environ.setdefault("DB__PASSWORD", "unused")
os.environ.setdefault("DB__NAME", "unused")
os.environ.setdefault("REDIS__HOST", "unused")
os.environ.setdefault("REDIS__PORT", "6379")
os.environ.setdefault("REDIS__DB", "0")

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from restaurant_database.base import BaseDBModel
from restaurant_security.rate_limiter import InMemoryRateLimiter
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from src.infrastructure.cache.token_blacklist import InMemoryTokenBlacklist
from src.presentation.api.v1 import dependencies as deps


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
    """Cliente HTTP com o app real, mas com DB (SQLite), blacklist e rate
    limiter (memória) isolados por teste."""
    # Import tardio (deliberado, ver PLC0415): só depois que as env vars de
    # config acima já foram setadas, já que `src.config.settings` é
    # instanciado no momento em que `src.main` é importado.
    from src.main import app  # noqa: PLC0415

    async def override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
        async with sqlite_session_factory() as session:
            yield session

    in_memory_blacklist = InMemoryTokenBlacklist()

    app.dependency_overrides[deps.get_db_session] = override_get_db_session
    app.dependency_overrides[deps.get_token_blacklist] = lambda: in_memory_blacklist
    app.dependency_overrides[deps.get_rate_limiter] = lambda: rate_limiter

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def tenant_id() -> uuid.UUID:
    return uuid.uuid4()
