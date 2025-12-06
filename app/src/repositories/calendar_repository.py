"""
CalendarRepository implementation for Calendar entity.

Provides CRUD operations and query methods for Calendar model.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.calendar import Calendar
from repositories.exceptions import CalendarNotFoundError
from repositories.schemas import NOT_SET, CalendarCreateSchema, CalendarFilter, CalendarResponse, CalendarUpdateSchema


class CalendarRepository:
    """Repository for Calendar entity operations.

    Provides methods for creating, reading, updating, and deleting calendars,
    as well as querying calendars with various filters.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize CalendarRepository with a database session.

        Args:
            session: SQLAlchemy async session to use for database operations.
        """
        self.session = session

    async def get_externals_to_sync(self) -> list[CalendarResponse]:
        """Retrieve external calendars.

        Returns:
            The list of external calendars if found, empty list otherwise.
        """
        result = await self.session.execute(select(Calendar).where(Calendar.url != None, Calendar.sync_enabled == True))  # noqa: E711, E712
        return [CalendarResponse.from_model(calendar) for calendar in result.scalars().all()]

    async def get_by_id(self, calendar_id: int) -> CalendarResponse | None:
        """Retrieve a calendar by its ID.

        Args:
            calendar_id: The ID of the calendar to retrieve.

        Returns:
            The calendar response if found, None otherwise.
        """
        result = await self.session.get(Calendar, calendar_id)
        if result is None:
            return None
        return CalendarResponse.from_model(result)

    async def create_one(self, data: CalendarCreateSchema) -> CalendarResponse:
        """Create a new calendar.

        Args:
            data: CalendarCreateSchema with calendar data.

        Returns:
            The created calendar as response.
        """
        calendar = Calendar(
            user_id=data.user_id,
            name=data.name,
            url=data.url,
        )
        self.session.add(calendar)
        await self.session.flush()
        await self.session.refresh(calendar)
        return CalendarResponse.from_model(calendar)

    async def update_by_id(self, calendar_id: int, data: CalendarUpdateSchema) -> CalendarResponse:
        """Update an existing calendar by ID.

        Args:
            calendar_id: The ID of the calendar to update.
            data: CalendarUpdateSchema with calendar data.

        Returns:
            The updated calendar response.
        """
        calendar_model = await self.session.get(Calendar, calendar_id)
        if calendar_model is None:
            raise CalendarNotFoundError(calendar_id=calendar_id)

        return await self._update_model(calendar_model, data)

    async def update_by_url(self, url: str, data: CalendarUpdateSchema) -> CalendarResponse:
        """Update a calendar by URL.

        Args:
            url: The URL of the calendar to update.
            data: CalendarUpdateSchema with calendar data.

        Returns:
            The updated calendar response.
        """
        calendar_model = await self.session.execute(select(Calendar).where(Calendar.url == url))
        if calendar_model is None:
            raise CalendarNotFoundError(calendar_id=None)

        return await self._update_model(calendar_model.scalar_one(), data)

    async def _update_model(self, calendar_model: Calendar, data: CalendarUpdateSchema) -> CalendarResponse:
        for field in data.__dataclass_fields__:
            value = getattr(data, field)
            if value is not NOT_SET:
                setattr(calendar_model, field, value)

        await self.session.flush()
        await self.session.refresh(calendar_model)
        return CalendarResponse.from_model(calendar_model)

    async def delete_by_id(self, calendar_id: int) -> None:
        """Delete a calendar by ID.

        Args:
            calendar_id: The ID of the calendar to delete.
        """
        calendar_model = await self.session.get(Calendar, calendar_id)
        if calendar_model is None:
            raise CalendarNotFoundError(calendar_id=calendar_id)
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

        conditions = [
            getattr(Calendar, field) == value for field, value in vars(filter).items() if value is not NOT_SET
        ]

        stmt = stmt.where(*conditions)
        result = await self.session.execute(stmt)
        return [CalendarResponse.from_model(calendar) for calendar in result.scalars().all()]
