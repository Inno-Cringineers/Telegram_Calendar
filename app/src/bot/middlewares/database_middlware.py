from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware

from bot.database import get_session


# middleware to inject database session in handlers
class DatabaseMiddleware(BaseMiddleware):
    def __init__(self, session_maker):
        super().__init__()  # required
        self.session_maker = session_maker  # database session maker

    # inject session in handler
    async def __call__(
        self,
        handler: Callable[[Any, dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: dict[str, Any],
    ) -> Any:
        async for session in get_session(self.session_maker):
            data["session"] = session
            result = await handler(event, data)
            await session.close()
            return result
