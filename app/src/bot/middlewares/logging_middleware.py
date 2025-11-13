from typing import Any, Callable, Dict, Awaitable, Union
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
import time

from bot.logger import logger


class MessageLoggingMiddleware(BaseMiddleware):
    """Middleware for logging message events."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """
        Log the message event and measure execution time.
        """
        if not isinstance(event, Message):
            return await handler(event, data)
        
        start_time = time.time()
        user_id = event.from_user.id if event.from_user else None
        user_name = event.from_user.full_name if event.from_user else None
        event_text = event.text or f"[{event.content_type}]"

        # Log incoming message
        logger.info(
            f"[message] User: {user_name} (ID: {user_id}) | Text: {event_text}"
        )

        try:
            # Call the handler
            result = await handler(event, data)
            
            # Log successful execution
            execution_time = time.time() - start_time
            logger.debug(f"Handler executed in {execution_time:.3f}s")
            
            return result
        except Exception as e:
            # Log error
            execution_time = time.time() - start_time
            logger.error(
                f"Error handling message from {user_name} (ID: {user_id}) "
                f"after {execution_time:.3f}s: {str(e)}",
                exc_info=True,
            )
            raise


class CallbackQueryLoggingMiddleware(BaseMiddleware):
    """Middleware for logging callback query events."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """
        Log the callback query event and measure execution time.
        """
        if not isinstance(event, CallbackQuery):
            return await handler(event, data)
        
        start_time = time.time()
        user_id = event.from_user.id
        user_name = event.from_user.full_name
        event_data = event.data or "no data"

        # Log incoming callback query
        logger.info(
            f"[callback_query] User: {user_name} (ID: {user_id}) | Data: {event_data}"
        )

        try:
            # Call the handler
            result = await handler(event, data)
            
            # Log successful execution
            execution_time = time.time() - start_time
            logger.debug(f"Handler executed in {execution_time:.3f}s")
            
            return result
        except Exception as e:
            # Log error
            execution_time = time.time() - start_time
            logger.error(
                f"Error handling callback_query from {user_name} (ID: {user_id}) "
                f"after {execution_time:.3f}s: {str(e)}",
                exc_info=True,
            )
            raise

