"""Event service for managing user events.

This service provides CRUD operations for user events using the event repository.
"""

from typing import TYPE_CHECKING

from repositories.schemas import (
    EventCreateSchema,
    EventDurationFilter,
    EventFilter,
    EventResponse,
    EventUpdateSchema,
)
from store.store import Store

if TYPE_CHECKING:
    pass


class EventService:
    """Service for managing user events.

    Provides CRUD operations for user events, using the event repository
    through the Store pattern.
    """

    def __init__(self, store: Store) -> None:
        """Initialize EventService with a store.

        Args:
            store: Store to use repositories and services.
        """
        self.store = store

    async def get_by_id(self, event_id: int) -> EventResponse | None:
        """Retrieve event by ID.

        Args:
            event_id: The ID of the event to retrieve.

        Returns:
            The event if found, None otherwise.
        """
        return await self.store.EventRepository.get_by_id(event_id)

    async def get_by_user_id(self, user_id: int) -> list[EventResponse]:
        """Retrieve events by user ID.

        Args:
            user_id: The Telegram user ID to find events for.

        Returns:
            The list of events if found, empty list otherwise.
        """
        return await self.store.EventRepository.find(EventFilter(user_id=user_id))

    async def get_by_calendar_id(self, calendar_id: int) -> list[EventResponse]:
        """Retrieve events by calendar ID.

        Args:
            calendar_id: The ID of the calendar to find events for.

        Returns:
            The list of events if found, empty list otherwise.
        """
        return await self.store.EventRepository.find(EventFilter(calendar_id=calendar_id))  # type: ignore[call-arg]

    async def find(self, filter: EventFilter) -> list[EventResponse]:
        """Find events matching the provided filter.

        Args:
            filter: EventFilter with filtering criteria.
        """
        return await self.store.EventRepository.find(filter)

    async def get_events_in_range(self, filter: EventDurationFilter) -> list[EventResponse]:
        """Get events that durates in this range.

        Args:
            filter: EventDurationFilter with filtering criteria.
        """
        return await self.store.EventRepository.find_by_duration(filter)

    async def create(
        self,
        data: EventCreateSchema,
    ) -> EventResponse:
        """Create new event for a user.

        Args:
            data: EventCreateSchema with event data.

        Returns:
            Created Event instance.
        """
        # create event
        created_event = await self.store.EventRepository.create_one(data)

        # create default reminder
        await self.store.ReminderService.create_default(created_event.id)

        return created_event

    async def update_by_id(
        self,
        event_id: int,
        data: EventUpdateSchema,
    ) -> EventResponse:
        """Update existing event.

        Args:
            event_id: The ID of the event to update.
            data: EventUpdateSchema with event data.

        Returns:
            Updated Event instance.

        Raises:
            EventNotFoundError: If event with given ID are not found.
        """
        # Get event before update to get user_id
        event = await self.store.EventRepository.get_by_id(event_id)
        if event is None:
            raise ValueError(f"Event with id {event_id} not found")

        updated_event = await self.store.EventRepository.update_by_id(event_id, data)
        # TODO: update reminders if needed

        return updated_event

    async def delete_by_id(self, event_id: int) -> None:
        """Delete event by ID.

        Args:
            event_id: The ID of the event to delete.

        Raises:
            EventNotFoundError: If event with given ID are not found.
        """
        # Get event before delete to get user_id
        event = await self.store.EventRepository.get_by_id(event_id)
        if event is None:
            raise ValueError(f"Event with id {event_id} not found")

        # delete reminders associated with the event
        await self.store.ReminderService.delete_by_event_id(event_id)
        await self.store.EventRepository.delete_by_id(event_id)

    async def delete_by_calendar_id(self, calendar_id: int) -> None:
        """Delete events by calendar ID.

        Args:
            calendar_id: The ID of the calendar to delete events for.
        """
        events = await self.get_by_calendar_id(calendar_id)
        for event in events:
            await self.delete_by_id(event.id)
