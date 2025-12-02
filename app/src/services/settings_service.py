"""Settings service for managing user settings.

This service provides CRUD operations for user settings using the settings repository.
"""

from datetime import time
from typing import TYPE_CHECKING

from repositories.schemas import SettingsCreateSchema, SettingsResponse, SettingsUpdateSchema
from store.store import Store

if TYPE_CHECKING:
    pass


class SettingsService:
    """Service for managing user settings.

    Provides CRUD operations for user settings, using the settings repository
    through the Store pattern.
    """

    def __init__(self, store: Store) -> None:
        """Initialize SettingsService with a store.

        Args:
            store: Store to use repositories and services.
        """
        self.store = store

    async def get_by_id(self, settings_id: int) -> SettingsResponse | None:
        """Retrieve settings by ID.

        Args:
            settings_id: The ID of the settings to retrieve.

        Returns:
            The settings if found, None otherwise.
        """
        return await self.store.SettingsRepository.get_by_id(settings_id)

    async def get_by_user_id(self, user_id: int) -> SettingsResponse | None:
        """Retrieve settings by user ID.

        Args:
            user_id: The Telegram user ID to find settings for.

        Returns:
            The settings if found, None otherwise.
        """
        return await self.store.SettingsRepository.find(user_id)

    async def create(
        self,
        user_id: int,
        timezone: str | None = None,
        language: str | None = None,
        quiet_hours: bool | None = None,
        quiet_hours_start: time | None = None,
        quiet_hours_end: time | None = None,
        daily_plans_time: time | None = None,
        default_reminder_offset: int | None = None,
    ) -> SettingsResponse:
        """Create new settings for a user.

        Args:
            user_id: Telegram user ID.
            timezone: User timezone. If None, uses default from config.
            language: User language. If None, uses default from config.
            quiet_hours: Whether quiet hours are enabled. If None, uses default from config.
            quiet_hours_start: Quiet hours start time. If None, uses default from config.
            quiet_hours_end: Quiet hours end time. If None, uses default from config.
            daily_plans_time: Daily plans time. If None, uses default from config.
            default_reminder_offset: Default reminder offset in seconds. If None, uses default from config.

        Returns:
            Created Settings instance.
        """
        from config.config import load_config

        config = load_config()
        settings_config = config.settings

        def _parse_time(time_str: str | None) -> time | None:
            """Parse time string in HH:MM format to time object.

            Args:
                time_str: Time string in "HH:MM" format, or None.

            Returns:
                time object or None if time_str is None.
            """
            if time_str is None:
                return None
            parts = time_str.split(":")
            if len(parts) != 2:
                raise ValueError(f"Invalid time format: {time_str}. Expected HH:MM")
            return time(hour=int(parts[0]), minute=int(parts[1]))

        create_schema = SettingsCreateSchema(
            user_id=user_id,
            timezone=timezone if timezone is not None else settings_config.timezone,
            language=language if language is not None else settings_config.language,
            quiet_hours=quiet_hours if quiet_hours is not None else settings_config.quiet_hours,
            quiet_hours_start=quiet_hours_start
            if quiet_hours_start is not None
            else _parse_time(settings_config.quiet_hours_start),
            quiet_hours_end=quiet_hours_end
            if quiet_hours_end is not None
            else _parse_time(settings_config.quiet_hours_end),
            daily_plans_time=daily_plans_time
            if daily_plans_time is not None
            else _parse_time(settings_config.daily_plans_time),
            default_reminder_offset=default_reminder_offset
            if default_reminder_offset is not None
            else settings_config.default_reminder_offset,
        )

        return await self.store.SettingsRepository.create(create_schema)

    async def create_default(self, user_id: int) -> SettingsResponse:
        """Create default settings for a user using config defaults.

        Args:
            user_id: Telegram user ID.

        Returns:
            Created Settings instance with default values from config.
        """
        return await self.create(user_id)

    async def update(
        self,
        settings_id: int,
        timezone: str | None = None,
        language: str | None = None,
        quiet_hours: bool | None = None,
        quiet_hours_start: time | None = None,
        quiet_hours_end: time | None = None,
        daily_plans_time: time | None = None,
        default_reminder_offset: int | None = None,
    ) -> SettingsResponse:
        """Update existing settings.

        Args:
            settings_id: The ID of the settings to update.
            timezone: New timezone value. If None, not updated.
            language: New language value. If None, not updated.
            quiet_hours: New quiet_hours value. If None, not updated.
            quiet_hours_start: New quiet_hours_start value. If None, not updated.
            quiet_hours_end: New quiet_hours_end value. If None, not updated.
            daily_plans_time: New daily_plans_time value. If None, not updated.
            default_reminder_offset: New default_reminder_offset value. If None, not updated.

        Returns:
            Updated Settings instance.

        Raises:
            SettingsNotFoundError: If settings with given ID are not found.
        """
        update_schema = SettingsUpdateSchema(
            timezone=timezone,
            language=language,
            quiet_hours=quiet_hours,
            quiet_hours_start=quiet_hours_start,
            quiet_hours_end=quiet_hours_end,
            daily_plans_time=daily_plans_time,
            default_reminder_offset=default_reminder_offset,
        )

        return await self.store.SettingsRepository.update(settings_id, update_schema)

    async def update_by_user_id(
        self,
        user_id: int,
        timezone: str | None = None,
        language: str | None = None,
        quiet_hours: bool | None = None,
        quiet_hours_start: time | None = None,
        quiet_hours_end: time | None = None,
        daily_plans_time: time | None = None,
        default_reminder_offset: int | None = None,
    ) -> SettingsResponse:
        """Update settings by user ID.

        First finds settings by user_id, then updates them.

        Args:
            user_id: Telegram user ID.
            timezone: New timezone value. If None, not updated.
            language: New language value. If None, not updated.
            quiet_hours: New quiet_hours value. If None, not updated.
            quiet_hours_start: New quiet_hours_start value. If None, not updated.
            quiet_hours_end: New quiet_hours_end value. If None, not updated.
            daily_plans_time: New daily_plans_time value. If None, not updated.
            default_reminder_offset: New default_reminder_offset value. If None, not updated.

        Returns:
            Updated Settings instance.

        Raises:
            SettingsNotFoundError: If settings for given user_id are not found.
        """
        settings = await self.get_by_user_id(user_id)
        if settings is None:
            from repositories.exceptions import SettingsNotFoundError

            raise SettingsNotFoundError(settings_id=user_id)

        return await self.update(
            settings.id,
            timezone=timezone,
            language=language,
            quiet_hours=quiet_hours,
            quiet_hours_start=quiet_hours_start,
            quiet_hours_end=quiet_hours_end,
            daily_plans_time=daily_plans_time,
            default_reminder_offset=default_reminder_offset,
        )

    async def delete(self, settings_id: int) -> None:
        """Delete settings by ID.

        Args:
            settings_id: The ID of the settings to delete.

        Raises:
            SettingsNotFoundError: If settings with given ID are not found.
        """
        await self.store.SettingsRepository.delete(settings_id)

    async def delete_by_user_id(self, user_id: int) -> None:
        """Delete settings by user ID.

        First finds settings by user_id, then deletes them.

        Args:
            user_id: Telegram user ID.

        Raises:
            SettingsNotFoundError: If settings for given user_id are not found.
        """
        settings = await self.get_by_user_id(user_id)
        if settings is None:
            from repositories.exceptions import SettingsNotFoundError

            raise SettingsNotFoundError(settings_id=user_id)

        await self.delete(settings.id)
