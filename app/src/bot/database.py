from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, declared_attr
from sqlalchemy.pool import StaticPool


# base class for models to inherit
class Base(DeclarativeBase):
    # Auto-generate __tablename__ from class name
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower()


# engine factory
def get_engine(db_url: str):
    # Check if using SQLite and ensure it uses aiosqlite driver
    is_sqlite = db_url.startswith("sqlite")
    if is_sqlite and "aiosqlite" not in db_url:
        # Convert sqlite:// to sqlite+aiosqlite://
        db_url = db_url.replace("sqlite://", "sqlite+aiosqlite://")

    # "check_same_thread : False" is required for sqlite in asyncio
    connect_args = {"check_same_thread": False} if is_sqlite else {}
    # create async engine for database
    engine = create_async_engine(
        db_url,  # database url
        echo=False,  # can be set to True for debugging
        future=True,  # required for asyncio
        poolclass=StaticPool if is_sqlite else None,  # required for sqlite
        connect_args=connect_args,  # required for sqlite
    )
    return engine


# session factory
def get_session_maker(engine):
    # create async session maker
    return async_sessionmaker(
        bind=engine,  # database engine
        expire_on_commit=False,  # required for asyncio
        class_=AsyncSession,  # required for asyncio
    )


# database initializer (creates tables)
async def init_db(engine):
    # needs to import models to register them
    from bot.models.event import Event

    # create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# dependency generator
# for example: async with get_session(session_maker) as session:
async def get_session(session_maker) -> AsyncGenerator[AsyncSession, None]:
    async with session_maker() as session:
        yield session
