"""
CalendarRepository implementation for Calendar entity.

Provides CRUD operations and query methods for Calendar model.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.calendar import Calendar
from repositories.base_repository import BaseRepository
from repositories.exceptions import CalendarNotFoundError
from repositories.schemas import CalendarCreateSchema, CalendarFilter, CalendarResponse, CalendarUpdateSchema

# TODO: Validation and exeptions


class CalendarRepository(BaseRepository[CalendarResponse]):
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

    async def get_by_id(self, entity_id: int) -> CalendarResponse | None:
        """Retrieve a calendar by its ID.

        Args:
            entity_id: The ID of the calendar to retrieve.

        Returns:
            The calendar response if found, None otherwise.
        """
        result = await self.session.get(Calendar, entity_id)
        if result is None:
            return None
        return CalendarResponse.from_model(result)

    async def create(self, data: list[CalendarCreateSchema], *args, **kwargs) -> list[CalendarResponse]:
        """Create a new calendar.

        Args:
            data: list of CalendarCreateSchema with calendar data.

        Returns:
            The created calendars as responses.
        """
        calendars = []
        for item in data:
            calendar = Calendar(
                user_id=item.user_id,
                name=item.name,
                url=item.url,
            )
            self.session.add(calendar)
            await self.session.flush()
            await self.session.refresh(calendar)
            calendars.append(CalendarResponse.from_model(calendar))
        return calendars

    async def update(self, entity_id: int, data: CalendarUpdateSchema, *args, **kwargs) -> CalendarResponse:
        """Update an existing calendar.

        Args:
            entity_id: The ID of the calendar to update.
            data: CalendarUpdateSchema with calendar data.

        Returns:
            The updated calendar response.
        """
        calendar_model = await self.session.get(Calendar, entity_id)
        if calendar_model is None:
            raise CalendarNotFoundError(calendar_id=entity_id)

        # Update only provided fields
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(calendar_model, key, value)
        await self.session.flush()

        await self.session.refresh(calendar_model)
        return CalendarResponse.from_model(calendar_model)

    async def delete(self, entity_id: int, *args, **kwargs) -> None:
        """Delete a calendar by ID.

        Args:
            entity_id: The ID of the calendar to delete.
        """
        calendar_model = await self.session.get(Calendar, entity_id)
        if calendar_model is None:
            raise CalendarNotFoundError(calendar_id=entity_id)
        await self.session.delete(calendar_model)
        await self.session.flush()

    async def find(self, filter: CalendarFilter) -> list[CalendarResponse]:
        """Find calendars matching the provided filter.

        Args:
            filter: CalendarFilter with filtering criteria.

        Returns:
            List of matching calendars as responses.
        """
        stmt = select(Calendar)

        # Apply filters
        if filter.user_id is not None:
            stmt = stmt.where(Calendar.user_id == filter.user_id)
        if filter.name is not None:
            stmt = stmt.where(Calendar.name == filter.name)
        if filter.url is not None:
            stmt = stmt.where(Calendar.url == filter.url)

        # limit and offset
        stmt = stmt.limit(filter.limit).offset(filter.offset)

        result = await self.session.execute(stmt)
        calendars = list(result.scalars().all())
        return [CalendarResponse.from_model(calendar) for calendar in calendars]
