"""Testes do `DatabaseManager` (engine assíncrona + ciclo de vida da sessão)."""

import pytest
from restaurant_database.session import DatabaseManager
from sqlalchemy import text


@pytest.mark.asyncio
async def test_session_context_manager_commits_on_success() -> None:
    manager = DatabaseManager("sqlite+aiosqlite:///:memory:")
    try:
        async with manager.session() as session:
            result = await session.execute(text("SELECT 1"))
            assert result.scalar_one() == 1
    finally:
        await manager.close()


@pytest.mark.asyncio
async def test_session_context_manager_rolls_back_and_reraises_on_exception() -> None:
    manager = DatabaseManager("sqlite+aiosqlite:///:memory:")
    try:
        with pytest.raises(RuntimeError, match="falha simulada"):
            async with manager.session():
                raise RuntimeError("falha simulada")
    finally:
        await manager.close()


@pytest.mark.asyncio
async def test_get_session_yields_a_usable_session_for_fastapi_dependency_injection() -> None:
    manager = DatabaseManager("sqlite+aiosqlite:///:memory:")
    try:
        generator = manager.get_session()
        session = await generator.__anext__()

        result = await session.execute(text("SELECT 1"))
        assert result.scalar_one() == 1

        with pytest.raises(StopAsyncIteration):
            await generator.__anext__()
    finally:
        await manager.close()
