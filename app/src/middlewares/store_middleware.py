"""
Aiogram middleware that creates Store and injects it into handler's data dict.

This middleware depends on DatabaseMiddleware (must be registered after it),
as it requires 'session' to be already present in data dict.
"""

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from logger.logger import logger
from store.store import Store


class StoreMiddleware(BaseMiddleware):
    """Middleware that creates Store and injects it into handler.

    This middleware must be registered AFTER DatabaseMiddleware,
    as it requires 'session' to be already present in data dict.

    Example:
        dp.message.middleware(DatabaseMiddleware(session_maker))
        dp.message.middleware(StoreMiddleware())  # After DatabaseMiddleware
    """

    async def __call__(
        self,
        handler: Callable[[Any, dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: dict[str, Any],
    ) -> Any:
        """Create Store and inject it into handler's data dict.

        Args:
            handler: The next handler to call.
            event: Incoming update/event object.
            data: Aiogram data dict which will receive 'store'.

        Returns:
            Whatever the handler returns.

        Raises:
            KeyError: If 'session' is not in data (DatabaseMiddleware not registered).
        """
        session: AsyncSession | None = data.get("session")
        if session is None:
            logger.error(
                "StoreMiddleware: 'session' not found in data. "
                "Make sure DatabaseMiddleware is registered before StoreMiddleware."
            )
            raise KeyError(
                "'session' not found in data. "
                "DatabaseMiddleware must be registered before StoreMiddleware."
            )

        logger.debug(
            "StoreMiddleware: creating Store for handler %s",
            getattr(handler, "__name__", repr(handler)),
        )
        store = Store(session)
        data["store"] = store

        result = await handler(event, data)

        logger.debug(
            "StoreMiddleware: handler completed %s",
            getattr(handler, "__name__", repr(handler)),
        )
        return result

