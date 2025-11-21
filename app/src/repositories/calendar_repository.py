"""
CalendarRepository implementation for Calendar entity.

Provides CRUD operations and query methods for Calendar model.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.calendar import Calendar
from repositories.base_repository import BaseRepository
from repositories.exceptions import CalendarNotFoundError
from repositories.schemas import CalendarCreateSchema, CalendarFilter, CalendarUpdateSchema


class CalendarRepository(BaseRepository[Calendar]):
    """Repository for Calendar entity operations.

    Provides methods for creating, reading, updating, and deleting calendars,
    as well as querying calendars with various filters.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize CalendarRepository with a database session.

        Args:
            session: SQLAlchemy async session to use for database operations.
        """
        super().__init__(session)

    async def get_by_id(self, entity_id: int) -> Calendar | None:
        """Retrieve a calendar by its ID.

        Args:
            entity_id: The ID of the calendar to retrieve.

        Returns:
            The calendar if found, None otherwise.
        """
        result = await self.session.get(Calendar, entity_id)
        return result

    async def create(self, data: CalendarCreateSchema, *args, **kwargs) -> Calendar:
        """Create a new calendar.

        Args:
            data: CalendarCreateSchema with calendar data.

        Returns:
            The created calendar.
        """
        calendar = Calendar(
            user_id=data.user_id,
            name=data.name,
            url=data.url,
        )
        self.session.add(calendar)
        await self.session.flush()
        return calendar

    async def update(self, entity_id: int, data: CalendarUpdateSchema, *args, **kwargs) -> Calendar:
        """Update an existing calendar.

        Args:
            entity_id: The ID of the calendar to update.
            data: CalendarUpdateSchema with calendar data.

        Returns:
            The updated calendar.
        """
        calendar = await self.get_by_id(entity_id)
        if calendar is None:
            raise CalendarNotFoundError(calendar_id=entity_id)

        # Update only provided fields
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(calendar, key, value)
        await self.session.flush()

        await self.session.refresh(calendar)
        return calendar

    async def delete(self, entity_id: int, *args, **kwargs) -> None:
        """Delete a calendar by ID.

        Args:
            entity_id: The ID of the calendar to delete.
        """
        calendar = await self.get_by_id(entity_id)
        if calendar is None:
            raise CalendarNotFoundError(calendar_id=entity_id)
        await self.session.delete(calendar)
        await self.session.flush()

    async def get_by_user_id(self, user_id: int) -> list[Calendar]:
        """Retrieve all calendars for a specific user.

        Args:
            user_id: The user ID to filter calendars by.

        Returns:
            List of calendars for the user.
        """
        stmt = select(Calendar).where(Calendar.user_id == user_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def find(self, filter: CalendarFilter) -> list[Calendar]:
        """Find calendars matching the provided filter.

        Args:
            filter: CalendarFilter with filtering criteria.

        Returns:
            List of matching calendars.
        """
        stmt = select(Calendar)

        # Apply filters
        if filter.user_id is not None:
            stmt = stmt.where(Calendar.user_id == filter.user_id)
        if filter.name is not None:
            stmt = stmt.where(Calendar.name == filter.name)
        if filter.url is not None:
            stmt = stmt.where(Calendar.url == filter.url)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())
