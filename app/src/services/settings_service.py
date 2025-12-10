"""Settings service for managing user settings.

This service provides CRUD operations for user settings using the settings repository.
"""

from datetime import time
from typing import TYPE_CHECKING

from repositories.exceptions import SettingsNotFoundError
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
        return await self.store.SettingsRepository.find_by_user_id(user_id)

    async def get_all_users(self) -> list[int]:
        """Retrieve all users.

        Returns:
            The list of users.
        """
        return await self.store.SettingsRepository.get_all_user_ids()

    async def create_default(
        self,
        user_id: int,
    ) -> SettingsResponse:
        """Create default settings for a user.

        Args:
            user_id: Telegram user ID.

        Returns:
            Created Settings instance with default values from config.
        """
        from config.config import load_config

        config = load_config()
        settings_config = config.settings

        def _parse_time(time_str: str) -> time:
            """Parse time string in HH:MM format to time object.

            Args:
                time_str: Time string in "HH:MM" format, or None.

            Returns:
                time object or None if time_str is None.
            """
            parts = time_str.split(":")
            if len(parts) != 2:
                raise ValueError(f"Invalid time format: {time_str}. Expected HH:MM")
            return time(hour=int(parts[0]), minute=int(parts[1]))

        create_schema = SettingsCreateSchema(
            user_id=user_id,
            timezone=settings_config.timezone,
            language=settings_config.language,
            quiet_hours_enabled=settings_config.quiet_hours_enabled,
            quiet_hours_start=_parse_time(settings_config.quiet_hours_start),
            quiet_hours_end=_parse_time(settings_config.quiet_hours_end),
            daily_plans_enabled=settings_config.daily_plans_enabled,
            daily_plans_time=_parse_time(settings_config.daily_plans_time),
            default_reminder_enabled=settings_config.default_reminder_enabled,
            default_reminder_offset=settings_config.default_reminder_offset,
        )

        created_settings = await self.store.SettingsRepository.create_one(create_schema)

        return created_settings

    async def update(self, settings_id: int, data: SettingsUpdateSchema) -> SettingsResponse:
        """Update existing settings.

        Args:
            settings_id: The ID of the settings to update.
            data: SettingsUpdateSchema with fields to update.

        Returns:
            Updated Settings instance.

        Raises:
            SettingsNotFoundError: If settings with given ID are not found.
        """
        updated_settings = await self.store.SettingsRepository.update_by_id(settings_id, data)
        return updated_settings

    async def update_by_user_id(
        self,
        user_id: int,
        data: SettingsUpdateSchema,
    ) -> SettingsResponse:
        """Update settings by user ID.

        First finds settings by user_id, then updates them.

        Args:
            user_id: Telegram user ID.
            data: SettingsUpdateSchema with fields to update.

        Returns:
            Updated Settings instance.

        Raises:
            SettingsNotFoundError: If settings for given user_id are not found.
        """
        settings = await self.get_by_user_id(user_id)
        if settings is None:
            raise SettingsNotFoundError(user_id=user_id)

        updated_settings = await self.update(
            settings.id,
            data,
        )
        return updated_settings

    async def switch_quiet_hours(self, user_id: int) -> SettingsResponse:
        """Switch quiet hours.

        Args:
            user_id: Telegram user ID.

        Returns:
            Updated Settings instance.
        """
        settings = await self.get_by_user_id(user_id)
        if settings is None:
            raise SettingsNotFoundError(user_id=user_id)

        return await self.update(
            settings.id, SettingsUpdateSchema(quiet_hours_enabled=not settings.quiet_hours_enabled)
        )

    async def switch_daily_plans(self, user_id: int) -> SettingsResponse:
        """Switch daily plans.

        Args:
            user_id: Telegram user ID.

        Returns:
            Updated Settings instance.
        """
        settings = await self.get_by_user_id(user_id)
        if settings is None:
            raise SettingsNotFoundError(user_id=user_id)

        return await self.update(
            settings.id, SettingsUpdateSchema(daily_plans_enabled=not settings.daily_plans_enabled)
        )

    async def delete(self, settings_id: int) -> None:
        """Delete settings by ID.

        Args:
            settings_id: The ID of the settings to delete.

        Raises:
            SettingsNotFoundError: If settings with given ID are not found.
        """
        await self.store.SettingsRepository.delete_by_id(settings_id)

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
            raise SettingsNotFoundError(user_id=user_id)

        await self.delete(settings.id)
