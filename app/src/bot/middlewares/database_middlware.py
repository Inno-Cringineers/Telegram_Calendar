from aiogram import BaseMiddleware
from typing import Callable, Dict, Any, Awaitable
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database import get_session

# middleware to inject database session in handlers
class DatabaseMiddleware(BaseMiddleware):
    def __init__(self, session_maker):
        super().__init__() # required
        self.session_maker = session_maker # database session maker

    # inject session in handler
    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: Dict[str, Any],
    ) -> Any:
        async for session in get_session(self.session_maker):
            data["session"] = session
            result = await handler(event, data)
            await session.close()
            return result
