"""
Middleware to inject async database session into aiogram handlers.
"""

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from database.database import AsyncSession, UnitOfWork, async_sessionmaker
from logger.logger import logger


# ------------------------------
# Aiogram Middleware
# ------------------------------
class DatabaseMiddleware(BaseMiddleware):
    """
    Middleware to inject async database session into aiogram handlers.

    Example:
        >>> dp.message.middleware(DatabaseMiddleware(SessionMaker))
    """

    def __init__(self, session_maker: async_sessionmaker[AsyncSession]):
        super().__init__()
        self.session_maker = session_maker

    async def __call__(
        self,
        handler: Callable[[Any, dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: dict[str, Any],
    ) -> Any:
        """
        Wrap handler call with UnitOfWork session and inject into data dict.
        """
        logger.debug("DatabaseMiddleware: entering handler %s", handler)
        async with UnitOfWork(self.session_maker) as session:
            data["session"] = session
            result = await handler(event, data)
        logger.debug("DatabaseMiddleware: exiting handler %s", handler)
        return result
