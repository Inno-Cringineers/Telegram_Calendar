"""
Aiogram middleware that injects a SQLAlchemy AsyncSession (via UnitOfWork)
into handler's data dict.

This middleware does NOT depend on Aiogram implementation details in tests:
tests can call the middleware directly with a mocked handler.
"""

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from aiogram import BaseMiddleware
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.database import UnitOfWork
from logger.logger import logger
from store.store import Store

if TYPE_CHECKING:
    pass


class StoreMiddleware(BaseMiddleware):
    """Middleware that creates a Store and injects it into handler.

    Example:
        dp.message.middleware(StoreMiddleware(session_maker))
    """

    def __init__(self, session_maker: async_sessionmaker[AsyncSession]):
        """Initialize middleware.

        Args:
            session_maker: async_sessionmaker that will be used to create a Store.
        """
        super().__init__()
        self.session_maker = session_maker

    async def __call__(
        self,
        handler: Callable[[Any, dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: dict[str, Any],
    ) -> Any:
        """Wrap handler invocation with UnitOfWork and inject 'store' into data.

        Args:
            handler: the next handler to call
            event: incoming update/event object
            data: aiogram data dict which will receive 'store'

        Returns:
            whatever the handler returns.
        """
        logger.debug("StoreMiddleware: entering handler %s", getattr(handler, "__name__", repr(handler)))
        async with UnitOfWork(self.session_maker) as uow:
            if uow.session is None:
                raise RuntimeError("UnitOfWork session is None")
            store = Store(uow.session)
            data["store"] = store
            result = await handler(event, data)
        logger.debug("StoreMiddleware: handler completed %s", getattr(handler, "__name__", repr(handler)))
        return result
