"""Gerenciador de Sessões Assíncronas do SQLAlchemy 2.0 (Async Engine).

Responsável pela criação do Pool de Conexões assíncrono e injeção do contexto
de tenant para suporte a Multi-Tenancy seguro.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


class DatabaseManager:
    """Gerenciador do ciclo de vida da engine e sessões do PostgreSQL."""

    def __init__(self, database_url: str, echo: bool = False) -> None:
        """Inicializa a AsyncEngine com otimização de Connection Pooling.

        Args:
            database_url: DSN do banco de dados (ex: postgresql+asyncpg://user:pass@host:5432/db).
            echo: Se True, imprime no stdout todas as queries SQL geradas (dev only).
        """
        pool_options: dict[str, Any] = {"pool_pre_ping": True}
        if not database_url.startswith("sqlite"):
            # SQLite (usado apenas em testes unitários de repositório via aiosqlite)
            # usa StaticPool/NullPool, que não aceitam pool_size/max_overflow/pool_recycle.
            pool_options["pool_size"] = 20
            pool_options["max_overflow"] = 10
            pool_options["pool_recycle"] = 1800  # Recicla conexões a cada 30 minutos

        self.engine: AsyncEngine = create_async_engine(database_url, echo=echo, **pool_options)
        self.session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

    async def close(self) -> None:
        """Encerra graciosamente todas as conexões do pool."""
        await self.engine.dispose()

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, Any]:
        """Gerenciador de contexto para criar uma sessão isolada com auto-rollback em caso de exceção.

        Uso fora do FastAPI (workers, scripts, testes):
            async with db_manager.session() as session:
                ...
        """
        async_session = self.session_factory()
        try:
            yield async_session
            await async_session.commit()
        except Exception:
            await async_session.rollback()
            raise
        finally:
            await async_session.close()

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Dependency FastAPI (`Depends(db_manager.get_session)`) que entrega uma sessão por requisição."""
        async with self.session() as async_session:
            yield async_session
