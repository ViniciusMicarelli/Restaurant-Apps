"""Fixtures dos testes de integração do `payment-service` (SQLite + Idempotency em memória)."""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator, Generator

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("PORT", "8007")
os.environ.setdefault("JWT_SECRET_KEY", "integration-test-secret-key-32chars")
os.environ.setdefault("DB__HOST", "unused")
os.environ.setdefault("DB__PORT", "5432")
os.environ.setdefault("DB__USER", "unused")
os.environ.setdefault("DB__PASSWORD", "unused")
os.environ.setdefault("DB__NAME", "unused")
os.environ.setdefault("REDIS__HOST", "unused")
os.environ.setdefault("REDIS__PORT", "6379")
os.environ.setdefault("REDIS__DB", "0")

import uuid

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from restaurant_database.base import BaseDBModel
from restaurant_security.rate_limiter import InMemoryRateLimiter
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from src.application.interfaces.repository_interface import OpenCommandInfo, PayableSummary
from src.infrastructure.cache.idempotency_store import InMemoryIdempotencyStore
from src.presentation.api.v1 import dependencies as deps


class StubDiningServiceClient:
    """Substitui `HttpxDiningServiceClient` nos testes de integração — evita
    bater numa rede real pro `dining-service` só pra validar a secret de QR
    Code + buscar a comanda aberta no autoatendimento do cliente (US-05.4).
    `valid` é mutável pelo próprio teste antes da chamada."""

    def __init__(self) -> None:
        self.valid = True
        self.open_command = OpenCommandInfo(command_id=uuid.uuid4(), service_fee_charged=False)

    async def get_open_command_for_table(
        self, *, tenant_id: uuid.UUID, table_number: int, secret: str
    ) -> OpenCommandInfo | None:
        del tenant_id, table_number, secret
        return self.open_command if self.valid else None


class StubOrderServiceClient:
    """Substitui `HttpxOrderServiceClient` — o total real dos pedidos da
    comanda, controlado pelo teste via `summary`."""

    def __init__(self) -> None:
        self.summary: PayableSummary | None = PayableSummary(
            total_amount=50.0, reference_order_id=uuid.uuid4()
        )

    async def get_payable_summary_for_command(
        self, *, tenant_id: uuid.UUID, command_id: uuid.UUID
    ) -> PayableSummary | None:
        del tenant_id, command_id
        return self.summary


class StubRestaurantServiceClient:
    """Substitui `HttpxRestaurantServiceClient` — taxa de serviço do
    tenant, controlada pelo teste via `fee_percent`."""

    def __init__(self) -> None:
        self.fee_percent: float | None = 0.0

    async def get_service_fee_percent(self, *, tenant_id: uuid.UUID) -> float | None:
        del tenant_id
        return self.fee_percent


@pytest_asyncio.fixture
async def sqlite_session_factory() -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(BaseDBModel.metadata.create_all)

    yield async_sessionmaker(bind=engine, expire_on_commit=False)

    await engine.dispose()


@pytest.fixture
def dining_service_client_stub() -> StubDiningServiceClient:
    return StubDiningServiceClient()


@pytest.fixture
def order_service_client_stub() -> StubOrderServiceClient:
    return StubOrderServiceClient()


@pytest.fixture
def restaurant_service_client_stub() -> StubRestaurantServiceClient:
    return StubRestaurantServiceClient()


@pytest.fixture
def rate_limiter() -> InMemoryRateLimiter:
    return InMemoryRateLimiter()


@pytest.fixture
def client(
    sqlite_session_factory: async_sessionmaker[AsyncSession],
    dining_service_client_stub: StubDiningServiceClient,
    order_service_client_stub: StubOrderServiceClient,
    restaurant_service_client_stub: StubRestaurantServiceClient,
    rate_limiter: InMemoryRateLimiter,
) -> Generator[TestClient, None, None]:
    from src.main import app  # noqa: PLC0415

    async def override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
        async with sqlite_session_factory() as session:
            yield session

    idempotency_store = InMemoryIdempotencyStore()

    app.dependency_overrides[deps.get_db_session] = override_get_db_session
    app.dependency_overrides[deps.get_idempotency_store] = lambda: idempotency_store
    app.dependency_overrides[deps.get_dining_service_client] = lambda: dining_service_client_stub
    app.dependency_overrides[deps.get_order_service_client] = lambda: order_service_client_stub
    app.dependency_overrides[deps.get_restaurant_service_client] = lambda: (
        restaurant_service_client_stub
    )
    app.dependency_overrides[deps.get_rate_limiter] = lambda: rate_limiter

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
