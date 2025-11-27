"""Tests for DatabaseMiddleware using mocks (no real Aiogram Dispatcher)."""

from typing import Any

import pytest
import pytest_asyncio
from sqlalchemy import select

from database.database import Base, get_engine, get_session_maker
from middlewares.database_middlware import DatabaseMiddleware

from ..test_database.test_database import DBTestModel


@pytest_asyncio.fixture
async def engine():
    engine = get_engine("sqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def session_maker(engine):
    return get_session_maker(engine)


@pytest.mark.asyncio
async def test_middleware_injects_session_and_commits(session_maker):
    """Ensure middleware injects session and commits when handler completes."""
    # Arrange
    mw = DatabaseMiddleware(session_maker)

    async def handler(event, data):
        session = data["session"]
        session.add(DBTestModel(id=10))
        return "ok"

    data: dict[str, Any] = {}

    # Act
    result = await mw(handler, event=None, data=data)

    # Assert
    assert result == "ok"
    assert "session" in data and data["session"] is not None

    # verify persistence
    async with session_maker() as session:
        res = await session.execute(select(DBTestModel).where(DBTestModel.id == 10))
        assert res.scalar() is not None


@pytest.mark.asyncio
async def test_middleware_rolls_back_on_handler_exception(session_maker):
    """Handler raises -> UnitOfWork must rollback and exception must propagate."""
    # Arrange
    mw = DatabaseMiddleware(session_maker)

    class Boom(Exception):
        pass

    async def bad_handler(event, data):
        session = data["session"]
        session.add(DBTestModel(id=11))
        raise Boom()

    # Act & Assert
    with pytest.raises(Boom):
        await mw(bad_handler, event=None, data={})

    # verify rollback occurred
    async with session_maker() as session:
        res = await session.execute(select(DBTestModel).where(DBTestModel.id == 11))
        assert res.scalar() is None
