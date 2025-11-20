"""
Aiogram middleware that injects a SQLAlchemy AsyncSession (via UnitOfWork)
into handler's data dict.

This middleware does NOT depend on Aiogram implementation details in tests:
tests can call the middleware directly with a mocked handler.
"""

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.database import UnitOfWork
from logger.logger import logger


class DatabaseMiddleware(BaseMiddleware):
    """Middleware that creates a UnitOfWork session and injects it into handler.

    Example:
        dp.message.middleware(DatabaseMiddleware(session_maker))
    """

    def __init__(self, session_maker: async_sessionmaker[AsyncSession]):
        """Initialize middleware.

        Args:
            session_maker: async_sessionmaker that will be used to create sessions.
        """
        super().__init__()
        self.session_maker = session_maker

    async def __call__(
        self,
        handler: Callable[[Any, dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: dict[str, Any],
    ) -> Any:
        """Wrap handler invocation with UnitOfWork and inject 'session' into data.

        Args:
            handler: the next handler to call
            event: incoming update/event object
            data: aiogram data dict which will receive 'session'

        Returns:
            whatever the handler returns.
        """
        logger.debug("DatabaseMiddleware: entering handler %s", getattr(handler, "__name__", repr(handler)))
        async with UnitOfWork(self.session_maker) as session:
            data["session"] = session
            result = await handler(event, data)
        logger.debug("DatabaseMiddleware: handler completed %s", getattr(handler, "__name__", repr(handler)))
        return result
