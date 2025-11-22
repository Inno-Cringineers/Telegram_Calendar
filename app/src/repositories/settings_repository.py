"""
SettingsRepository implementation for Settings entity.

Provides CRUD operations and query methods for Settings model.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.settings import Settings
from repositories.base_repository import BaseRepository
from repositories.exceptions import SettingsNotFoundError
from repositories.schemas import SettingsCreateSchema, SettingsUpdateSchema


class SettingsRepository(BaseRepository[Settings]):
    def __init__(self, session: AsyncSession) -> None:
        """Initialize SettingsRepository with a database session.

        Args:
            session: SQLAlchemy async session to use for database operations.
        """
        super().__init__(session)

    async def get_by_id(self, entity_id: int) -> Settings | None:
        """Retrieve a settings by its ID.

        Args:
            entity_id: The ID of the settings to retrieve.

        Returns:
            The settings if found, None otherwise.
        """
        result = await self.session.get(Settings, entity_id)
        return result

    async def get_by_user_id(self, user_id: int) -> Settings | None:
        """Retrieve a settings by user ID.

        Args:
            user_id: The user ID to filter settings by.

        Returns:
            The settings if found, None otherwise.
        """
        result = await self.session.execute(select(Settings).where(Settings.user_id == user_id))
        return result.scalar_one_or_none()

    async def create(self, data: SettingsCreateSchema, *args, **kwargs) -> Settings:
        """Create a new settings.

        Args:
            data: The data to create the settings with.
        """
        settings = Settings(
            user_id=data.user_id,
            timezone=data.timezone,
            language=data.language,
            quiet_hours_start=data.quiet_hours_start,
            quiet_hours_end=data.quiet_hours_end,
            daily_plans_time=data.daily_plans_time,
            default_reminder_offset=data.default_reminder_offset,
        )
        self.session.add(settings)
        await self.session.flush()
        return settings

    async def update(self, entity_id: int, data: SettingsUpdateSchema, *args, **kwargs) -> Settings:
        """Update an existing settings.

        Args:
            entity_id: The ID of the settings to update.
            data: The data to update the settings with.
        """
        settings = await self.get_by_id(entity_id)
        if settings is None:
            raise SettingsNotFoundError(settings_id=entity_id)

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(settings, key, value)

        await self.session.flush()
        await self.session.refresh(settings)
        return settings

    async def delete(self, entity_id: int, *args, **kwargs) -> None:
        """Delete a settings by ID.

        Args:
            entity_id: The ID of the settings to delete.
        """
        settings = await self.get_by_id(entity_id)
        if settings is None:
            raise SettingsNotFoundError(settings_id=entity_id)
        await self.session.delete(settings)
        await self.session.flush()
