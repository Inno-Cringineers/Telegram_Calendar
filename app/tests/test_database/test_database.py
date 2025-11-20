"""Unit tests for database utils and UnitOfWork."""

import pytest
import pytest_asyncio
from sqlalchemy import Integer, select
from sqlalchemy.orm import Mapped, mapped_column

from src.database.database import Base, UnitOfWork, get_engine, get_session_maker, normalize_db_url


class DBTestModel(Base):
    """Simple model with integer PK for tests."""

    id: Mapped[int] = mapped_column(Integer, primary_key=True)


def test_normalize_db_url_sqlite_memory():
    assert normalize_db_url("sqlite:///:memory:") == "sqlite+aiosqlite:///:memory:"


def test_normalize_db_url_sqlite_file():
    assert normalize_db_url("sqlite:///file.db") == "sqlite+aiosqlite:///file.db"


def test_normalize_db_url_postgres_untouched():
    url = "postgresql+asyncpg://user:pass@localhost/db"
    assert normalize_db_url(url) == url


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
    async with UnitOfWork(session_maker) as session:
        session.add(DBTestModel(id=1))

    # After context exits, data must be persisted
    async with session_maker() as session:
        res = await session.execute(select(DBTestModel).where(DBTestModel.id == 1))
        assert res.scalar() is not None


@pytest.mark.asyncio
async def test_uow_rollback_on_exception(session_maker):
    class Boom(Exception):
        pass

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
    async with session_maker() as session:
        session.add(DBTestModel(id=3))
        await session.commit()

    async with session_maker() as session:
        res = await session.execute(select(DBTestModel).where(DBTestModel.id == 3))
        assert res.scalar() is not None
