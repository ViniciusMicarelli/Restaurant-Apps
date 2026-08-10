"""Fixtures compartilhadas dos testes de `restaurant_database`.

Usa SQLite em memória (via `aiosqlite`) para testar o comportamento do
repositório genérico sem depender de um PostgreSQL real de pé — os testes de
integração específicos de cada microsserviço (contra Postgres de verdade)
ficam em `tests/integration/` dentro de cada serviço.
"""

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from restaurant_database.base import BaseDBModel, TenantAwareModel
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Mapped, mapped_column


class SampleWidget(TenantAwareModel):
    """Modelo de exemplo usado apenas nos testes do pacote `restaurant_database`."""

    __tablename__ = "sample_widgets"

    name: Mapped[str] = mapped_column()


@pytest_asyncio.fixture
async def sqlite_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(BaseDBModel.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture
def sample_widget_model() -> type[SampleWidget]:
    return SampleWidget
