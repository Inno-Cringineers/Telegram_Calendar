"""
Async database utilities for SQLAlchemy.

Provides:
- Base declarative class with automatic table naming
- normalize_db_url: convert Postgresql URLs to async driver form
- get_engine: create async engine (Postgresql and other DBs)
- get_session_maker: create async_sessionmaker
- init_db: import models and create tables
- UnitOfWork: async context manager for transactional sessions
"""

from typing import Any, ClassVar

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, declared_attr

from logger.logger import logger


class Base(DeclarativeBase):
    """Base class for ORM models with automatic lowercased table names.

    NOTE:
        ``declared_attr`` returning a ``str`` may confuse some type-checkers
        (mypy / pylance). We keep the simple pattern and ignore overly-strict
        type checks where needed.
    """

    __allow_unmapped__: ClassVar[bool] = True

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """Generate table name from class name (lowercased)."""
        return cls.__name__.lower()


def normalize_db_url(db_url: str) -> str:
    """Normalize DB URL to async-compatible variant.

    For PostgreSQL URLs that don't already include an async driver, replace the
    scheme to use asyncpg.

    Args:
        db_url: Original DB connection URL.

    Returns:
        Async-compatible DB URL.
    """
    if db_url.startswith("postgresql://") and "+asyncpg" not in db_url:
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
    return db_url


def create_engine(db_url: str) -> AsyncEngine:
    """Create an async SQLAlchemy engine.

    For PostgreSQL URLs that don't already include an async driver, replace the
    scheme to use asyncpg.

    Args:
        db_url: Database connection URL.

    Returns:
        AsyncEngine: configured SQLAlchemy async engine.
    """
    db_url = normalize_db_url(db_url)

    return create_async_engine(db_url, echo=False, future=True)


def create_session_maker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create an async session factory (async_sessionmaker).

    Args:
        engine: AsyncEngine returned by :func:`create_engine`.

    Returns:
        async_sessionmaker bound to the engine.
    """
    return async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def create_tables(engine: AsyncEngine) -> None:
    """Import models and create database tables.

    Args:
        engine: AsyncEngine created via :func:`create_engine`.
    """
    # Import models to register them with SQLAlchemy metadata.
    # Add any other model modules that should be included.
    try:
        # Import known models (if they exist in your project)
        from models.calendar import Calendar  # noqa: F401 # pyright: ignore[reportUnusedImport]
        from models.event import Event  # noqa: F401 # pyright: ignore[reportUnusedImport]
        from models.reminder import Reminder  # noqa: F401 # pyright: ignore[reportUnusedImport]
        from models.settings import Settings  # noqa: F401 # pyright: ignore[reportUnusedImport]
    except Exception:
        # If project does not have those modules yet, skip — tests can import test models
        logger.debug("Some model imports failed during init_db (maybe not present in test env).")

    logger.debug("Initializing database schema")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized")


class UnitOfWork:
    """Async context manager to provide a transactional session.

    Usage:
        async with UnitOfWork(session_maker) as session:
            session.add(obj)
            # commit on exit, rollback on exception

    The UnitOfWork:
    - opens an AsyncSession
    - begins a transaction
    - commits the transaction if the block exits normally
    - rolls back if an exception occurs
    - always closes the session
    """

    def __init__(self, session_maker: async_sessionmaker[AsyncSession]):
        """Initialize UnitOfWork with a session factory.

        Args:
            session_maker: async_sessionmaker producing AsyncSession instances.
        """
        self.session_maker = session_maker
        self.session: AsyncSession | None = None

    async def __aenter__(self) -> "UnitOfWork":
        """Enter context: create session and begin transaction.

        Returns:
            UnitOfWork: UnitOfWork instance to use inside the context.
        """
        self.session = self.session_maker()
        logger.debug("UnitOfWork: opening session and beginning transaction")
        # begin a transaction
        # TODO: возможно begin тут лишний и его стоит убрать, т.к. в сессии уже есть транзакция
        await self.session.begin()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Exit context: commit or rollback, then close the session."""
        if self.session is None:
            raise RuntimeError("UnitOfWork session was not created")

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
