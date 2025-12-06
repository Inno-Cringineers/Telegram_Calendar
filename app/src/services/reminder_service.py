"""Reminder service for managing user reminders.

This service provides CRUD operations for user reminders using the reminder repository.
"""

from datetime import timedelta
from typing import TYPE_CHECKING

from icalendar import vDuration

from repositories.schemas import (
    ReminderCreateSchema,
    ReminderFilter,
    ReminderResponse,
    ReminderUpdateSchema,
)
from store.store import Store

if TYPE_CHECKING:
    pass


class ReminderService:
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

    async def get_by_id(self, reminder_id: int) -> ReminderResponse | None:
        """Retrieve reminder by ID.

        Args:
            reminder_id: The ID of the reminder to retrieve.

        Returns:
            The reminder if found, None otherwise.
        """
        return await self.store.ReminderRepository.get_by_id(reminder_id)

    async def find(self, filter: ReminderFilter) -> list[ReminderResponse]:
        """Find reminders matching the provided filter.

        Args:
            filter: ReminderFilter with filtering criteria.

        Returns:
            The list of reminders if found, empty list otherwise.
        """
        return await self.store.ReminderRepository.find(filter)

    async def create(
        self,
        data: ReminderCreateSchema,
    ) -> ReminderResponse:
        """Create new reminder for an event.

        Args:
            data: ReminderCreateSchema with reminder data.

        Returns:
            Created Reminder instance.
        """
        created_reminder = await self.store.ReminderRepository.create_one(data)
        return created_reminder

    async def create_default(self, event_id: int) -> ReminderResponse:
        """Create default reminder for an event.

        Args:
            event_id: The ID of the event to create reminder for.
        """
        event = await self.store.EventService.get_by_id(event_id)
        if event is None:
            raise ValueError(f"Event with id {event_id} not found")
        settings = await self.store.SettingsService.get_by_user_id(event.user_id)
        if settings is None:
            raise ValueError(f"Settings with user id {event.user_id} not found")
        default_reminder_offset = settings.default_reminder_offset
        trigger_offset = vDuration(timedelta(seconds=-default_reminder_offset)).to_ical().decode("utf-8")
        return await self.create(
            ReminderCreateSchema(
                event_id=event_id, description="Default reminder", trigger_offset=trigger_offset, sent=False
            )
        )

    async def update(
        self,
        reminder_id: int,
        data: ReminderUpdateSchema,
    ) -> ReminderResponse:
        """Update existing reminder.

        Args:
            reminder_id: The ID of the reminder to update.
            data: ReminderUpdateSchema with fields to update.

        Returns:
            Updated Reminder instance.
        """
        return await self.store.ReminderRepository.update_by_id(reminder_id, data)

    async def delete_by_id(self, reminder_id: int) -> None:
        """Delete reminder by ID.

        Args:
            reminder_id: The ID of the reminder to delete.

        Raises:
            ReminderNotFoundError: If reminder with given ID are not found.
        """
        await self.store.ReminderRepository.delete_by_id(reminder_id)

    async def delete_by_event_id(self, event_id: int) -> None:
        """Delete reminders by event ID.

        Args:
            event_id: The ID of the event to delete reminders for.
        """
        reminders = await self.find(ReminderFilter(event_id=event_id))
        for reminder in reminders:
            await self.delete_by_id(reminder.id)
