"""
SettingsRepository implementation for Settings entity.

Provides CRUD operations and query methods for Settings model.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.settings import Settings
from repositories.exceptions import SettingsNotFoundError
from repositories.schemas import NOT_SET, SettingsCreateSchema, SettingsResponse, SettingsUpdateSchema


class SettingsRepository:
    def __init__(self, session: AsyncSession) -> None:
        """Initialize SettingsRepository with a database session.

        Args:
            session: SQLAlchemy async session to use for database operations.
        """
        self.session = session

    async def get_by_id(self, settings_id: int) -> SettingsResponse | None:
        """Retrieve a settings by its ID.

        Args:
            settings_id: The ID of the settings to retrieve.

        Returns:
            The settings response if found, None otherwise.
        """
        result = await self.session.get(Settings, settings_id)
        if result is None:
            return None
        return SettingsResponse.from_model(result)

    async def create_one(self, data: SettingsCreateSchema) -> SettingsResponse:
        """Create a new settings.

        Args:
            data: SettingsCreateSchema with settings data.

        Returns:
            Created settings response.
        """
        settings = Settings(
            user_id=data.user_id,
            timezone=data.timezone,
            language=data.language,
            quiet_hours_enabled=data.quiet_hours_enabled,
            quiet_hours_start=data.quiet_hours_start,
            quiet_hours_end=data.quiet_hours_end,
            daily_plans_enabled=data.daily_plans_enabled,
            daily_plans_time=data.daily_plans_time,
            default_reminder_offset=data.default_reminder_offset,
        )
        self.session.add(settings)
        await self.session.flush()
        await self.session.refresh(settings)
        return SettingsResponse.from_model(settings)

    async def update_by_id(self, settings_id: int, data: SettingsUpdateSchema) -> SettingsResponse:
        """Update an existing settings.

        Args:
            settings_id: The ID of the settings to update.
            data: The data to update the settings with.

        Returns:
            Updated settings response.
        """
        settings_model = await self.session.get(Settings, settings_id)
        if settings_model is None:
            raise SettingsNotFoundError(settings_id=settings_id)

        return await self._update_model(settings_model, data)

    async def _update_model(self, settings_model: Settings, data: SettingsUpdateSchema) -> SettingsResponse:
        for field in data.__dataclass_fields__:
            value = getattr(data, field)
            if value is not NOT_SET:
                setattr(settings_model, field, value)

        await self.session.flush()
        await self.session.refresh(settings_model)
        return SettingsResponse.from_model(settings_model)

    async def find_by_user_id(self, user_id: int) -> SettingsResponse | None:
        """Find settings by user ID.

        Args:
            user_id: The ID of the user to find settings for.

        Returns:
            The settings response if found, None otherwise.
        """
        result = await self.session.execute(select(Settings).where(Settings.user_id == user_id))
        settings_model = result.scalar()
        if settings_model is None:
            return None
        return SettingsResponse.from_model(settings_model)

    async def delete_by_id(self, settings_id: int) -> None:
        """Delete a settings by ID.

        Args:
            settings_id: The ID of the settings to delete.
        """
        settings_model = await self.session.get(Settings, settings_id)
        if settings_model is None:
            raise SettingsNotFoundError(settings_id=settings_id)
        await self.session.delete(settings_model)
        await self.session.flush()
