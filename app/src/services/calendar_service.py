"""Calendar service for managing user calendars.

This service provides CRUD operations for user calendars using the calendar repository.
"""

from typing import TYPE_CHECKING

from repositories.schemas import (
    CalendarCreateSchema,
    CalendarFilter,
    CalendarResponse,
    CalendarUpdateSchema,
)
from store.store import Store

if TYPE_CHECKING:
    pass


class CalendarService:
    """Service for managing user calendars.

    Provides CRUD operations for user calendars, using the calendar repository
    through the Store pattern.
    """

    def __init__(self, store: Store) -> None:
        """Initialize CalendarService with a store.

        Args:
            store: Store to use repositories and services.
        """
        self.store = store

    async def get_by_id(self, calendar_id: int) -> CalendarResponse | None:
        """Retrieve calendar by ID.

        Args:
            calendar_id: The ID of the calendar to retrieve.

        Returns:
            The calendar if found, None otherwise.
        """
        return await self.store.CalendarRepository.get_by_id(calendar_id)

    async def get_by_user_id(self, user_id: int) -> list[CalendarResponse]:
        """Retrieve calendar by user ID.

        Args:
            user_id: The Telegram user ID to find calendar for.

        Returns:
            The list of calendars if found, empty list otherwise.
        """
        return await self.store.CalendarRepository.find(CalendarFilter(user_id=user_id))

    async def get_externals_to_sync(self) -> list[CalendarResponse]:
        """Retrieve external calendars.

        Returns:
            The list of external calendars if found, empty list otherwise.
        """
        return await self.store.CalendarRepository.get_externals_to_sync()

    async def get_external_calendars_by_user_id(self, user_id: int) -> list[CalendarResponse]:
        """Retrieve external calendars by user ID.

        Args:
            user_id: The Telegram user ID to find external calendars for.

        Returns:
            The list of external calendars if found, empty list otherwise.
        """
        calendars = await self.store.CalendarRepository.find(CalendarFilter(user_id=user_id))
        return [calendar for calendar in calendars if calendar.url is not None]

    async def find(self, filter: CalendarFilter) -> list[CalendarResponse]:
        """Find calendars matching the provided filter.

        Args:
            filter: CalendarFilter with filtering criteria.

        Returns:
            The list of calendars if found, empty list otherwise.
        """
        return await self.store.CalendarRepository.find(filter)

    async def create(
        self,
        data: CalendarCreateSchema,
    ) -> CalendarResponse:
        """Create new calendar for a user.

        Args:
            data: CalendarCreateSchema with calendar data.

        Returns:
            Created Calendar instance.
        """
        if data.url is None and data.name != "local calendar":
            raise ValueError("URL is required for external calendars.")
        return await self.store.CalendarRepository.create_one(data)

    async def update(
        self,
        calendar_id: int,
        data: CalendarUpdateSchema,
    ) -> CalendarResponse:
        """Update existing calendar.

        Args:
            calendar_id: The ID of the calendar to update.
            data: CalendarUpdateSchema with calendar data.

        Returns:
            Updated Calendar instance.

        Raises:
            CalendarNotFoundError: If calendar with given ID are not found.
        """
        if data.name == "local calendar":
            raise ValueError("local calendar name is reserved.")
        return await self.store.CalendarRepository.update_by_id(calendar_id, data)

    async def delete(self, calendar_id: int) -> None:
        """Delete calendar by ID.

        Args:
            calendar_id: The ID of the calendar to delete.

        Raises:
            CalendarNotFoundError: If calendar with given ID are not found.
        """
        # delete events and reminders associated with the calendar
        await self.store.EventService.delete_by_calendar_id(calendar_id)
        await self.store.CalendarRepository.delete_by_id(calendar_id)
