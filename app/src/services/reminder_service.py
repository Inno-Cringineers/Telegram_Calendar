"""Reminder service for managing user reminders.

This service provides CRUD operations for user reminders using the reminder repository.
"""

from datetime import timedelta
from typing import TYPE_CHECKING

from icalendar import vDuration

from repositories.schemas import (
    EventFilter,
    ReminderCreateSchema,
    ReminderFilter,
    ReminderResponse,
    ReminderUpdateSchema,
)
from store.store import Store

if TYPE_CHECKING:
    pass


def _normalize_trigger_offset(trigger_offset: str) -> str:
    """Normalize trigger_offset to ensure it's negative (before event).

    Args:
        trigger_offset: RFC 5545 trigger offset string.

    Returns:
        Normalized trigger offset string with negative sign.
    """
    if not trigger_offset.startswith("-"):
        trigger_offset = "-" + trigger_offset
    return trigger_offset


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

    async def create_default(self, event_id: int) -> ReminderResponse | None:
        """Create default reminder for an event.

        Args:
            event_id: The ID of the event to create reminder for.

        Returns:
            Created Reminder instance if default reminder is enabled, None otherwise.
        """
        event = await self.store.EventService.get_by_id(event_id)
        if event is None:
            raise ValueError(f"Event with id {event_id} not found")
        settings = await self.store.SettingsService.get_by_user_id(event.user_id)
        if settings is None:
            raise ValueError(f"Settings with user id {event.user_id} not found")
        if not settings.default_reminder_enabled:
            return None

        # Check if default reminder already exists
        existing_reminders = await self.find(ReminderFilter(event_id=event_id))
        has_default = any(r.description == "Default reminder" for r in existing_reminders)
        if has_default:
            return None

        default_reminder_offset = settings.default_reminder_offset
        trigger_offset = vDuration(timedelta(seconds=default_reminder_offset)).to_ical().decode("utf-8")
        trigger_offset = _normalize_trigger_offset(trigger_offset)
        created_reminder = await self.create(
            ReminderCreateSchema(
                event_id=event_id,
                description="Default reminder",
                trigger_offset=trigger_offset,
            )
        )
        return created_reminder

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
        # Get reminder before update to get event_id
        reminder = await self.store.ReminderRepository.get_by_id(reminder_id)
        if reminder is None:
            raise ValueError(f"Reminder with id {reminder_id} not found")

        updated_reminder = await self.store.ReminderRepository.update_by_id(reminder_id, data)

        return updated_reminder

    async def delete_by_id(self, reminder_id: int) -> None:
        """Delete reminder by ID.

        Args:
            reminder_id: The ID of the reminder to delete.

        Raises:
            ReminderNotFoundError: If reminder with given ID are not found.
        """
        # Get reminder before delete to get event_id
        reminder = await self.store.ReminderRepository.get_by_id(reminder_id)
        if reminder is None:
            raise ValueError(f"Reminder with id {reminder_id} not found")

        await self.store.ReminderRepository.delete_by_id(reminder_id)

    async def delete_by_event_id(self, event_id: int) -> None:
        """Delete reminders by event ID.

        Args:
            event_id: The ID of the event to delete reminders for.
        """
        # Get event to get user_id before deleting reminders
        event = await self.store.EventService.get_by_id(event_id)
        if event is None:
            return

        reminders = await self.find(ReminderFilter(event_id=event_id))
        for reminder in reminders:
            await self.store.ReminderRepository.delete_by_id(reminder.id)

    async def delete_default_reminders_by_user_id(self, user_id: int) -> None:
        """Delete all default reminders for a user.

        Args:
            user_id: The user ID to delete default reminders for.
        """
        await self.store.ReminderRepository.delete_by_description_and_user_id("Default reminder", user_id)

    async def restore_default_reminders_for_user(self, user_id: int) -> None:
        """Restore default reminders for all user's events.

        Args:
            user_id: The user ID to restore default reminders for.
        """
        settings = await self.store.SettingsService.get_by_user_id(user_id)
        if settings is None or not settings.default_reminder_enabled:
            return

        # Get all events for the user
        events = await self.store.EventService.find(EventFilter(user_id=user_id))  # type: ignore[call-arg]
        default_reminder_offset = settings.default_reminder_offset
        trigger_offset = vDuration(timedelta(seconds=default_reminder_offset)).to_ical().decode("utf-8")
        trigger_offset = _normalize_trigger_offset(trigger_offset)

        for event in events:
            # Check if default reminder already exists
            existing_reminders = await self.find(ReminderFilter(event_id=event.id))
            default_reminder = next((r for r in existing_reminders if r.description == "Default reminder"), None)

            if default_reminder is None:
                # Create new default reminder
                await self.create(
                    ReminderCreateSchema(
                        event_id=event.id,
                        description="Default reminder",
                        trigger_offset=trigger_offset,
                    )
                )
            else:
                # Update existing default reminder with new offset
                await self.update(
                    default_reminder.id,
                    ReminderUpdateSchema(trigger_offset=trigger_offset),
                )

    async def update_default_reminders_for_user(self, user_id: int) -> None:
        """Update all default reminders for a user with new offset.

        Args:
            user_id: The user ID to update default reminders for.
        """
        settings = await self.store.SettingsService.get_by_user_id(user_id)
        if settings is None or not settings.default_reminder_enabled:
            return

        # Get all events for the user
        events = await self.store.EventService.find(EventFilter(user_id=user_id))  # type: ignore[call-arg]
        default_reminder_offset = settings.default_reminder_offset
        trigger_offset = vDuration(timedelta(seconds=default_reminder_offset)).to_ical().decode("utf-8")
        trigger_offset = _normalize_trigger_offset(trigger_offset)

        for event in events:
            # Get all reminders for this event
            existing_reminders = await self.find(ReminderFilter(event_id=event.id))
            default_reminder = next((r for r in existing_reminders if r.description == "Default reminder"), None)

            if default_reminder is not None:
                # Update existing default reminder with new offset
                await self.update(
                    default_reminder.id,
                    ReminderUpdateSchema(trigger_offset=trigger_offset),
                )
            else:
                # Create new default reminder if it doesn't exist
                await self.create(
                    ReminderCreateSchema(
                        event_id=event.id,
                        description="Default reminder",
                        trigger_offset=trigger_offset,
                    )
                )
