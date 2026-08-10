"""Ambiente de execução do Alembic para o `delivery-service` (SQLAlchemy 2.0 Async)."""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from restaurant_database.base import BaseDBModel
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from src.config import settings
from src.infrastructure.models.delivery_model import DeliveryModel  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = BaseDBModel.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=settings.db.async_dsn,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def _do_run_migrations(connection: object) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)  # type: ignore[arg-type]
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    engine: AsyncEngine = create_async_engine(settings.db.async_dsn)
    async with engine.connect() as connection:
        await connection.run_sync(_do_run_migrations)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
