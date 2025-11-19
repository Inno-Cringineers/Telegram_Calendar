"""
Async database module for SQLAlchemy + Aiogram integration.

Features:
- Async engine creation with SQLite and PostgreSQL support
- Async session factory (async_sessionmaker)
- UnitOfWork context manager for automatic commit/rollback
- DatabaseMiddleware for injecting session into aiogram handlers
- Logging via src.bot.logger

Usage:

    >>> from src.bot.database import get_engine, get_session_maker
    >>> engine = get_engine("sqlite:///:memory:")
    >>> SessionMaker = get_session_maker(engine)

    >>> # Using UnitOfWork
    >>> async with UnitOfWork(SessionMaker) as session:
    >>>     session.add(obj)
    >>>     # commit automatically, rollback on exception

    >>> # Using DatabaseMiddleware with Aiogram
    >>> dp.message.middleware(DatabaseMiddleware(SessionMaker))
"""

# TODO: CHECK IS ALL GOOD, REFACTOR IF NEEDED, WRITE TESTS
from typing import Any

from logger.logger import logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, declared_attr
from sqlalchemy.pool import StaticPool


# ------------------------------
# Base ORM class
# ------------------------------
class Base(DeclarativeBase):
    """Base class for all ORM models with auto-generated table names."""

    @declared_attr.directive
    def __tablename__(cls: Any) -> str:
        """Automatically generate table name from class name in lowercase."""
        return cls.__name__.lower()


# ------------------------------
# Engine and session setup
# ------------------------------
def normalize_db_url(db_url: str) -> str:
    """
    Convert DB URL to async-compatible version.

    Example:
        'sqlite:///:memory:' -> 'sqlite+aiosqlite:///:memory:'
    """
    if db_url.startswith("sqlite://") and "+aiosqlite" not in db_url:
        db_url = db_url.replace("sqlite://", "sqlite+aiosqlite://")
    return db_url


def get_engine(db_url: str):
    """
    Create async SQLAlchemy engine with logging.

    Args:
        db_url: database connection string.

    Returns:
        Async engine.
    """
    db_url = normalize_db_url(db_url)
    is_sqlite = db_url.startswith("sqlite")
    connect_args = {"check_same_thread": False} if is_sqlite else {}

    logger.debug("Creating async engine for %s", db_url)
    return create_async_engine(
        db_url,
        echo=False,
        future=True,
        poolclass=StaticPool if is_sqlite else None,
        connect_args=connect_args,
    )


def get_session_maker(engine) -> async_sessionmaker[AsyncSession]:
    """
    Create async session factory (maker).

    Args:
        engine: SQLAlchemy async engine.

    Returns:
        async_sessionmaker
    """
    return async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def init_db(engine) -> None:
    """
    Initialize database tables.

    Args:
        engine: SQLAlchemy async engine.
    """
    from src.bot.models.calendar import Calendar  # noqa: F401
    from src.bot.models.event import Event  # noqa: F401
    from src.bot.models.reminder import Reminder  # noqa: F401
    from src.bot.models.settings import Settings  # noqa: F401

    logger.debug("Initializing database")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized")


# ------------------------------
# UnitOfWork
# ------------------------------
class UnitOfWork:
    """
    Async context manager for managing session + transaction.

    Usage:
        async with UnitOfWork(session_maker) as session:
            session.add(obj)
            # commit automatically, rollback on exception
    """

    def __init__(self, session_maker: async_sessionmaker[AsyncSession]):
        self.session_maker = session_maker
        self.session: AsyncSession | None = None

    async def __aenter__(self) -> AsyncSession:
        self.session = self.session_maker()
        logger.debug("UnitOfWork: starting session and transaction")
        await self.session.begin()
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session is None:
            return
        try:
            if exc_type:
                logger.warning("UnitOfWork: exception detected, rolling back: %s", exc_val)
                await self.session.rollback()
            else:
                logger.debug("UnitOfWork: committing transaction")
                await self.session.commit()
        finally:
            await self.session.close()
            logger.debug("UnitOfWork: session closed")
