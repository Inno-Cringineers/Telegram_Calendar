"""Unit tests for database utils and UnitOfWork."""

import pytest
import pytest_asyncio
from sqlalchemy import Integer, select
from sqlalchemy.orm import Mapped, mapped_column

from database.database import Base, UnitOfWork, get_engine, get_session_maker, normalize_db_url


class DBTestModel(Base):
    """Simple model with integer PK for tests."""

    id: Mapped[int] = mapped_column(Integer, primary_key=True)


def test_normalize_db_url_sqlite_memory():
    # Arrange
    url = "sqlite:///:memory:"

    # Act
    result = normalize_db_url(url)

    # Assert
    assert result == "sqlite+aiosqlite:///:memory:"


def test_normalize_db_url_sqlite_file():
    # Arrange
    url = "sqlite:///file.db"

    # Act
    result = normalize_db_url(url)

    # Assert
    assert result == "sqlite+aiosqlite:///file.db"


def test_normalize_db_url_postgres_untouched():
    # Arrange
    url = "postgresql+asyncpg://user:pass@localhost/db"

    # Act
    result = normalize_db_url(url)

    # Assert
    assert result == url


@pytest_asyncio.fixture
async def engine():
    """Create an async engine and ensure tables are created for tests."""
    engine = get_engine("sqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def session_maker(engine):
    return get_session_maker(engine)


@pytest.mark.asyncio
async def test_uow_commit_persists(session_maker):
    # Arrange & Act
    async with UnitOfWork(session_maker) as session:
        session.add(DBTestModel(id=1))

    # Assert
    async with session_maker() as session:
        res = await session.execute(select(DBTestModel).where(DBTestModel.id == 1))
        assert res.scalar() is not None


@pytest.mark.asyncio
async def test_uow_rollback_on_exception(session_maker):
    # Arrange
    class Boom(Exception):
        pass

    # Act & Assert
    with pytest.raises(Boom):
        async with UnitOfWork(session_maker) as session:
            session.add(DBTestModel(id=2))
            raise Boom()

    # Ensure the insert was rolled back
    async with session_maker() as session:
        res = await session.execute(select(DBTestModel).where(DBTestModel.id == 2))
        assert res.scalar() is None


@pytest.mark.asyncio
async def test_session_maker_direct_usage(session_maker):
    # Arrange & Act
    async with session_maker() as session:
        session.add(DBTestModel(id=3))
        await session.commit()

    # Assert
    async with session_maker() as session:
        res = await session.execute(select(DBTestModel).where(DBTestModel.id == 3))
        assert res.scalar() is not None
