"""Import service for importing events from icalendar files."""

import uuid
from datetime import UTC, date, datetime, time, timedelta
from typing import TYPE_CHECKING

from icalendar.prop import vDuration

from repositories.schemas import (
    CalendarCreateSchema,
    CalendarFilter,
    CalendarResponse,
    EventCreateSchema,
    EventFilter,
    EventResponse,
    EventUpdateSchema,
    ReminderCreateSchema,
)
from services.ics_parcer import ICSParser, VAlarmSchema, VEventSchema
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
        # check if calendar already exists
        calendar = await self._get_local_calendar(user_id)
        if calendar is None:
            # Create local calendar if it doesn't exist
            calendar = await self.store.CalendarService.create(
                CalendarCreateSchema(user_id=user_id, name="local calendar", url=None)
            )

        # loading entities from file using ICSParser
        schemas = ICSParser(file_path).get_schemas()

        # updating calendar
        await self._update_local_calendar(calendar, schemas)

    async def _get_local_calendar(self, user_id: int) -> CalendarResponse | None:
        """Get local calendar by user ID.

        Args:
            user_id: Telegram user ID.
        """
        # Get local calendar by user ID
        calendars = await self.store.CalendarService.get_by_user_id(user_id)
        for calendar in calendars:
            if calendar.name == "local calendar":
                return calendar
        return None

    async def _update_local_calendar(self, calendar: CalendarResponse, schemas: list[VEventSchema]) -> None:
        """Update existing local calendar with new events.

        Args:
            calendar: CalendarResponse to update.
            schemas: List of VEventSchema to import.
        """
        for schema in schemas:
            await self._create_event(calendar, schema)

    async def _create_event(self, calendar: CalendarResponse, schema: VEventSchema) -> None:
        """Create a new event in the database.

        Args:
            calendar: CalendarResponse to create the event for.
            schema: VEventSchema to create the event from.
        """
        # check if event already exists in this calendar - then update it
        # Filter by both uid and calendar_id to ensure events are user-specific
        event = await self.store.EventService.find(EventFilter(uid=schema.uid, calendar_id=calendar.id))  # type: ignore[call-arg]
        if event != []:
            updated_event = await self.store.EventService.update_by_id(
                event[0].id,
                EventUpdateSchema(
                    date_start=schema.date_start,
                    date_end=schema.date_end,
                    all_day=self._is_all_day(schema.date_start, schema.date_end),
                    need_to_remind=True,
                    rrule=schema.rrule,
                    rdate=schema.rdate,
                    exdate=schema.exdate,
                    title=schema.title,
                    description=schema.description,
                ),
            )
            # delete reminders associated with the event
            # await self.store.ReminderService.delete_by_event_id(event[0].id)
            # create reminders from schema alarms
            if schema.alarms is not None:
                for alarm in schema.alarms:
                    await self._create_reminder(updated_event, alarm)
            # Create default reminder if enabled and doesn't exist
            await self.store.ReminderService.create_default(updated_event.id)
            return

        event = EventCreateSchema(
            user_id=calendar.user_id,
            calendar_id=calendar.id,
            uid=schema.uid if schema.uid is not None else await self._generate_uid(calendar.id),
            date_start=schema.date_start,
            date_end=schema.date_end,
            all_day=self._is_all_day(schema.date_start, schema.date_end),
            need_to_remind=True,
            rrule=schema.rrule,
            rdate=schema.rdate,
            exdate=schema.exdate,
            title=schema.title,
            description=schema.description,
        )
        created_event = await self.store.EventService.create(event)
        if schema.alarms is not None:
            for alarm in schema.alarms:
                await self._create_reminder(created_event, alarm)

    async def _create_reminder(self, event: EventResponse, alarm: VAlarmSchema) -> None:
        """Create a new reminder in the database, only for future occurrences."""
        trigger_offset = alarm.trigger_offset

        if trigger_offset is None:
            if alarm.trigger_datetime is None:
                return
            # вычисляем offset из trigger_datetime
            delta = alarm.trigger_datetime - event.date_start
            trigger_offset = vDuration(delta).to_ical().decode("utf-8")

        # Нормализуем offset: убеждаемся, что он отрицательный (напоминание до события)
        if not trigger_offset.startswith("-"):
            trigger_offset = "-" + trigger_offset

        # Парсим offset в timedelta
        delta = vDuration.from_ical(trigger_offset)  # timedelta

        # Момент отправки напоминания
        reminder_datetime = event.date_start + delta

        # Скипаем прошедшие
        if reminder_datetime <= datetime.now(UTC):
            return

        # Сохраняем
        reminder = ReminderCreateSchema(
            event_id=event.id,
            description=alarm.description,
            trigger_offset=trigger_offset,
        )
        await self.store.ReminderService.create(reminder)

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
        schemas = ICSParser(file_path).get_schemas()
        # checking if calendar already exists
        calendar = await self.store.CalendarService.find(CalendarFilter(user_id=user_id, url=calendar_url))
        if calendar == []:
            calendar = await self.store.CalendarService.create(
                CalendarCreateSchema(user_id=user_id, name=calendar_name, url=calendar_url)
            )
        else:
            calendar = calendar[0]

        # updating calendar
        await self._update_external_calendar(calendar, schemas)

    async def _update_external_calendar(self, calendar: CalendarResponse, schemas: list[VEventSchema]) -> None:
        """Update existing external calendar with new events.

        Args:
            calendar: CalendarResponse to update.
            schemas: List of VEventSchema to import.
        """
        for schema in schemas:
            schema.alarms = None
            await self._create_event(calendar, schema)

    async def _generate_uid(self, calendar_id: int) -> str:
        """Generate a unique UID for an event within a calendar.

        Generates UUID4 and checks if it already exists in the specified calendar.
        Retries up to 1000 times before raising an error.

        Args:
            calendar_id: The calendar ID to check uniqueness within.

        Returns:
            Unique UID string within the calendar.

        Raises:
            ValueError: If unable to generate a unique UID after 1000 attempts.
        """
        event_service = self.store.EventService
        for _ in range(1000):
            uid = str(uuid.uuid4())
            # Check uniqueness within the calendar, not globally
            if not await event_service.find(EventFilter(uid=uid, calendar_id=calendar_id)):  # type: ignore[call-arg]
                return uid
        raise ValueError("Failed to generate unique ID for event")

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
