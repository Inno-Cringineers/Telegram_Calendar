"""Settings middleware that ensures user settings exist.

This middleware checks if settings exist for a user, and if not, creates default settings
using the SettingsService. It works with both Message and CallbackQuery events.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import time
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from logger.logger import logger
from store.store import Store


@dataclass
class SettingsData:
    lang: str
    timezone: str
    quiet_hours_enabled: bool
    quiet_hours_start: time
    quiet_hours_end: time
    daily_plans_enabled: bool
    daily_plans_time: time
    default_reminder_enabled: bool
    default_reminder_offset: int


class SettingsMiddleware(BaseMiddleware):
    """Middleware that ensures user settings exist.

    Checks if settings exist for the user from the event, and if not,
    creates default settings using SettingsService.

    Example:
        dp.message.middleware(SettingsMiddleware())
        dp.callback_query.middleware(SettingsMiddleware())
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """Ensure user settings exist before calling handler.

        Args:
            handler: The next handler to call.
            event: Incoming update/event object (Message or CallbackQuery).
            data: Aiogram data dict which should contain 'store'.

        Returns:
            Whatever the handler returns.
        """
        # Extract user_id from event
        user_id: int | None = None
        if isinstance(event, Message) and event.from_user:
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery) and event.from_user:
            user_id = event.from_user.id

        # If no user_id, skip settings check but still set default lang
        if user_id is None:
            logger.debug("SettingsMiddleware: No user_id found, skipping settings check")
            data["lang"] = "en"
            return await handler(event, data)

        # Get store from data (should be injected by StoreMiddleware)
        store: Store | None = data.get("store")
        if store is None:
            logger.error("SettingsMiddleware: Store not found in data, skipping settings check")
            data["lang"] = "en"
            return await handler(event, data)

        # Check if settings exist
        settings_service = store.SettingsService
        settings = await settings_service.get_by_user_id(user_id)

        if settings is None:
            # Create default settings
            logger.info(f"SettingsMiddleware: Creating default settings for user {user_id}")
            try:
                settings = await settings_service.create_default(user_id)
                logger.debug(f"SettingsMiddleware: Default settings created for user {user_id}")
            except Exception as e:
                logger.error(
                    f"SettingsMiddleware: Failed to create default settings for user {user_id}: {str(e)}",
                    exc_info=True,
                )
                # Continue anyway - don't block the handler
                # Use default language if settings creation failed
                data["lang"] = "en"
                return await handler(event, data)

        logger.debug(f"SettingsMiddleware: Settings found for user {user_id}")

        # Inject language into data dict for handlers (similar to how store is injected)
        # Handlers can access it via parameter: lang: str or via data.get("lang")
        data["lang"] = settings.language

        # add settings to data
        data["timezone"] = settings.timezone

        data["settings"] = SettingsData(
            lang=settings.language,
            timezone=settings.timezone,
            quiet_hours_enabled=settings.quiet_hours_enabled,
            quiet_hours_start=settings.quiet_hours_start,
            quiet_hours_end=settings.quiet_hours_end,
            daily_plans_enabled=settings.daily_plans_enabled,
            daily_plans_time=settings.daily_plans_time,
            default_reminder_enabled=settings.default_reminder_enabled,
            default_reminder_offset=settings.default_reminder_offset,
        )

        # Call the handler
        return await handler(event, data)
