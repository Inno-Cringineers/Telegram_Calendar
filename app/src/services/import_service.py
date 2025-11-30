"""Import service for importing events from icalendar files."""

import uuid
from datetime import date, datetime, time, timedelta
from typing import TYPE_CHECKING

from icalendar.prop import vDuration

from models.calendar import Calendar
from models.event import Event
from models.reminder import Reminder
from repositories.schemas import (
    CalendarCreateSchema,
    CalendarFilter,
    EventCreateSchema,
    EventFilter,
    EventUpdateSchema,
    ReminderCreateSchema,
)
from services.ics_parcer import ICSParser
from store.store import Store

if TYPE_CHECKING:
    pass


class ImportService:
    """Import service for importing events from icalendar files.

    This service handles importing calendar events from iCalendar (.ics) files,
    supporting both local and external calendar imports. It manages event creation,
    updates, and reminder synchronization.
    """

    def __init__(self, store: Store) -> None:
        """Initialize ImportService with a store.

        Args:
            store: Store to use repositories and services.
        """
        self.store = store

    async def import_local_calendar_from_file(
        self,
        file_path: str,
        user_id: int,
    ) -> None:
        """Import local calendar from icalendar file.

        Args:
            file_path: Path to the icalendar file.
            user_id: telegram user id.
        """
        # loading entities from file using ICSParser
        entities = ICSParser(file_path).get_entities()

        # check if calendar already exists
        filter = CalendarFilter(user_id=user_id, name="local calendar")  # type: ignore[call-arg]
        calendar = await self.store.get_calendar_repository.find(filter)
        if calendar != []:
            # updating calendar if it exists
            await self._update_local_calendar(calendar[0], entities)
        else:
            # creating calendar if it does not exist
            await self._create_local_calendar(user_id, entities)

    async def _create_local_calendar(self, user_id: int, entities: list[tuple[Event, list[Reminder]]]) -> None:
        """Create a new local calendar and import all events with reminders.

        Args:
            user_id: Telegram user ID.
            entities: List of tuples containing (Event, list[Reminder]) to import.
        """
        calendar_repo = self.store.get_calendar_repository

        # Create local calendar
        calendar = await calendar_repo.create([CalendarCreateSchema(user_id=user_id, name="local calendar", url=None)])
        calendar = calendar[0]

        # Import each event with its reminders
        for event, reminders in entities:
            # Create event
            created_event = await self._create_event(
                user_id=user_id,
                calendar_id=calendar.id,
                event=event,
            )

            # Create imported reminders
            await self._create_reminders(event_id=created_event.id, reminders=reminders)

            # Create default reminder if user has default reminder offset configured
            await self._create_default_reminder(
                user_id=user_id,
                event_id=created_event.id,
                event_start=created_event.date_start,
            )

    async def _update_local_calendar(self, calendar: Calendar, entities: list[tuple[Event, list[Reminder]]]) -> None:
        """Update existing local calendar with new events and reminders.

        For each entity:
        - If event with same UID exists, update it and replace all reminders
        - If event doesn't exist, create it with reminders

        Args:
            calendar: Calendar to update.
            entities: List of tuples containing (Event, list[Reminder]) to import.
        """
        event_repo = self.store.get_event_repository
        reminder_repo = self.store.get_reminder_repository

        for new_event, new_reminders in entities:
            # Find existing event by UID
            filter = EventFilter(uid=new_event.uid)  # type: ignore[call-arg]
            old_events = await event_repo.find(filter)

            if old_events == []:
                # Create new event if it doesn't exist
                created_event = await self._create_event(
                    user_id=calendar.user_id,
                    calendar_id=calendar.id,
                    event=new_event,
                )
                event_id = created_event.id
            else:
                # Update existing event
                event_id = old_events[0].id
                await self._update_event(event_id=event_id, event=new_event)

                # Delete old reminders before creating new ones
                old_reminders = await reminder_repo.find(event_id)
                if old_reminders is not None:
                    for reminder in old_reminders:
                        await reminder_repo.delete(reminder.id)

            # Create imported reminders
            await self._create_reminders(event_id=event_id, reminders=new_reminders)

            # Create default reminder if user has default reminder offset configured
            await self._create_default_reminder(
                user_id=calendar.user_id,
                event_id=event_id,
                event_start=new_event.date_start,
            )

    async def import_external_calendar_from_file(
        self,
        file_path: str,
        user_id: int,
        calendar_name: str,
        calendar_url: str,
    ) -> None:
        """Import calendar from icalendar file.

        Args:
            file_path: Path to the icalendar file.
            user_id: Telegram user ID.
            calendar_name: Name of the calendar.
            calendar_url: URL of the calendar.
        """

        # loading entities from file using ICSParser
        entities = ICSParser(file_path).get_entities()

        calendar_repo = self.store.get_calendar_repository

        filter = CalendarFilter(user_id=user_id, name=calendar_name)  # type: ignore[call-arg]
        calendar = await calendar_repo.find(filter)
        if calendar != []:
            if calendar[0].url != calendar_url:
                raise ValueError("Calendar with this name already exists, but with different url")

        filter = CalendarFilter(user_id=user_id, url=calendar_url)  # type: ignore[call-arg]
        calendar = await calendar_repo.find(filter)
        if calendar != []:
            if calendar[0].name != calendar_name:
                raise ValueError("Calendar with this url already exists, but with different name")
            else:
                await self._update_external_calendar(calendar[0], entities)
        else:
            await self._create_external_calendar(user_id, calendar_name, calendar_url, entities)

    async def _create_external_calendar(
        self, user_id: int, calendar_name: str, calendar_url: str, entities: list[tuple[Event, list[Reminder]]]
    ) -> None:
        """Create a new external calendar and import events (without reminders).

        Note: Reminders are not imported from external calendars in this version.

        Args:
            user_id: Telegram user ID.
            calendar_name: Name of the calendar.
            calendar_url: URL of the external calendar.
            entities: List of tuples containing (Event, list[Reminder]) to import.
        """
        calendar_repo = self.store.get_calendar_repository

        # Create external calendar
        calendar = await calendar_repo.create(
            [CalendarCreateSchema(user_id=user_id, name=calendar_name, url=calendar_url)]
        )
        calendar = calendar[0]

        # Import events (reminders are not imported from external calendars)
        for event, _reminders in entities:
            await self._create_event(
                user_id=user_id,
                calendar_id=calendar.id,
                event=event,
            )

    async def _update_external_calendar(self, calendar: Calendar, entities: list[tuple[Event, list[Reminder]]]) -> None:
        """Update external calendar by deleting all existing events and importing new ones.

        Note: Reminders are not imported from external calendars in this version.
        This method performs a full replacement of all events in the calendar.

        Args:
            calendar: Calendar to update.
            entities: List of tuples containing (Event, list[Reminder]) to import.
        """
        event_repo = self.store.get_event_repository

        # Delete all existing events in the calendar
        events = await event_repo.find(EventFilter(calendar_id=calendar.id))  # type: ignore[call-arg]
        if events != []:
            for event in events:
                await event_repo.delete(event.id)

        # Create new events (reminders are not imported from external calendars)
        for event, _reminders in entities:
            await self._create_event(
                user_id=calendar.user_id,
                calendar_id=calendar.id,
                event=event,
            )

    async def _generate_uid(self) -> str:
        """Generate a unique UID for an event.

        Generates UUID4 and checks if it already exists in the database.
        Retries up to 1000 times before raising an error.

        Returns:
            Unique UID string.

        Raises:
            ValueError: If unable to generate a unique UID after 1000 attempts.
        """
        event_repo = self.store.get_event_repository
        for _ in range(1000):
            uid = str(uuid.uuid4())
            if not await event_repo.find(EventFilter(uid=uid)):  # type: ignore[call-arg]
                return uid
        raise ValueError("Failed to generate unique ID for event or reminder")

    def _is_all_day(self, dtstart: date | datetime, dtend: date | datetime) -> bool:
        """Check if an event is an all-day event.

        An event is considered all-day if:
        1. dtstart is a date (not datetime), or
        2. Both dtstart and dtend are datetimes at midnight (00:00:00)
           and the duration is a multiple of 24 hours.

        Args:
            dtstart: Event start date or datetime.
            dtend: Event end date or datetime.

        Returns:
            True if the event is all-day, False otherwise.
        """
        # If start is a date (not datetime), it's an all-day event
        if isinstance(dtstart, date) and not isinstance(dtstart, datetime):
            return True

        # Check if both are datetimes and aligned to midnight with full-day duration
        if isinstance(dtstart, datetime) and isinstance(dtend, datetime):
            return (
                dtstart.time() == time(0, 0)
                and dtend.time() == time(0, 0)
                and (dtend - dtstart) % timedelta(days=1) == timedelta(0)
            )

        return False

    def _build_event_create_schema(
        self, user_id: int, calendar_id: int, event: Event, uid: str | None
    ) -> EventCreateSchema:
        """Build EventCreateSchema from Event model.

        Args:
            user_id: Telegram user ID.
            calendar_id: Calendar ID to associate the event with.
            event: Event model to convert.
            uid: UID for the event (generated if None).

        Returns:
            EventCreateSchema instance.
        """
        return EventCreateSchema(
            user_id=user_id,
            calendar_id=calendar_id,
            uid=uid,
            date_start=event.date_start,
            date_end=event.date_end,
            all_day=self._is_all_day(event.date_start, event.date_end),
            need_to_remind=True,
            rrule=event.rrule,
            rdate=event.rdate,
            exdate=event.exdate,
            title=event.title,
            description=event.description,
        )

    async def _create_event(self, user_id: int, calendar_id: int, event: Event) -> Event:
        """Create a new event in the database.

        Args:
            user_id: Telegram user ID.
            calendar_id: Calendar ID to associate the event with.
            event: Event model to create.

        Returns:
            Created Event instance.
        """
        uid = event.uid if event.uid is not None else await self._generate_uid()
        event_schema = self._build_event_create_schema(user_id=user_id, calendar_id=calendar_id, event=event, uid=uid)
        created_events = await self.store.get_event_repository.create([event_schema])
        return created_events[0]

    def _build_event_update_schema(self, event: Event) -> EventUpdateSchema:
        """Build EventUpdateSchema from Event model.

        Args:
            event: Event model to convert.

        Returns:
            EventUpdateSchema instance.
        """
        return EventUpdateSchema(
            date_start=event.date_start,
            date_end=event.date_end,
            all_day=self._is_all_day(event.date_start, event.date_end),
            need_to_remind=True,
            rrule=event.rrule,
            rdate=event.rdate,
            exdate=event.exdate,
            title=event.title,
            description=event.description,
        )

    async def _update_event(self, event_id: int, event: Event) -> None:
        """Update an existing event in the database.

        Args:
            event_id: ID of the event to update.
            event: Event model with new data.
        """
        update_schema = self._build_event_update_schema(event)
        await self.store.get_event_repository.update(event_id, update_schema)

    async def _create_reminders(self, event_id: int, reminders: list[Reminder]) -> None:
        """Create reminders for an event.

        Args:
            event_id: ID of the event to create reminders for.
            reminders: List of Reminder models to create.
        """
        for reminder in reminders:
            await self.store.get_reminder_repository.create(
                [
                    ReminderCreateSchema(
                        event_id=event_id,
                        description=reminder.description,
                        trigger_offset=reminder.trigger_offset,
                        trigger_datetime=reminder.trigger_datetime,
                        repeat_count=reminder.repeat_count,
                        repeat_interval=reminder.repeat_interval,
                    )
                ]
            )

    async def _create_default_reminder(self, user_id: int, event_id: int, event_start: datetime) -> None:
        """Create a default reminder for an event based on user settings.

        If the user has a default_reminder_offset configured in their settings,
        creates a reminder using trigger_offset (RFC 5545 format).

        Args:
            user_id: Telegram user ID to get settings for.
            event_id: ID of the event to create reminder for.
            event_start: Start datetime of the event.
        """
        settings_repo = self.store.get_settings_repository
        settings = await settings_repo.get_by_id(user_id)

        if settings is not None and settings.default_reminder_offset is not None:
            # Convert seconds to RFC 5545 duration format (e.g., "-PT15M" for 15 minutes before)
            trigger_offset = vDuration(timedelta(seconds=-settings.default_reminder_offset)).to_ical().decode("utf-8")

            await self.store.get_reminder_repository.create(
                [
                    ReminderCreateSchema(
                        event_id=event_id,
                        description="Default reminder",
                        trigger_offset=trigger_offset,
                        trigger_datetime=None,
                        repeat_count=None,
                        repeat_interval=None,
                    )
                ]
            )
