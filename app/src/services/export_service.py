"""Export service for exporting events to icalendar files."""

import tempfile
from datetime import UTC, date, datetime
from pathlib import Path

import icalendar
from icalendar import Event as ICalEvent

from logger.logger import logger
from repositories.schemas import EventResponse
from store.store import Store


class ExportService:
    """Export service for exporting events to iCalendar (.ics) files.

    This service handles exporting calendar events to iCalendar format,
    supporting all event properties including recurrence rules.
    """

    def __init__(self, store: Store) -> None:
        """Initialize ExportService with a store.

        Args:
            store: Store to use repositories and services.
        """
        self.store = store

    async def export_local_calendar_to_file(self, user_id: int) -> str:
        """Export local calendar events to icalendar file.

        Args:
            user_id: Telegram user ID.

        Returns:
            Path to the generated .ics file.

        Raises:
            ValueError: If local calendar not found or has no events.
        """
        # Get local calendar
        calendar = await self._get_local_calendar(user_id)
        if calendar is None:
            raise ValueError("Local calendar not found")

        # Get all events from local calendar
        events = await self.store.EventService.get_by_calendar_id(calendar.id)
        if not events:
            raise ValueError("No events in local calendar")

        # Create iCalendar object
        cal = icalendar.Calendar()
        cal.add("prodid", "-//Telegram Calendar Bot//EN")
        cal.add("version", "2.0")

        # Add all events
        for event in events:
            vevent = self._event_to_vevent(event)
            cal.add_component(vevent)

        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".ics")
        temp_file.write(cal.to_ical())
        temp_file.close()

        logger.info(f"Exported {len(events)} events to {temp_file.name} for user {user_id}")
        return temp_file.name

    async def _get_local_calendar(self, user_id: int):
        """Get local calendar by user ID.

        Args:
            user_id: Telegram user ID.

        Returns:
            CalendarResponse if found, None otherwise.
        """
        calendars = await self.store.CalendarService.get_by_user_id(user_id)
        for calendar in calendars:
            if calendar.name == "local calendar":
                return calendar
        return None

    def _event_to_vevent(self, event: EventResponse) -> ICalEvent:
        """Convert EventResponse to iCalendar VEVENT.

        Args:
            event: EventResponse to convert.

        Returns:
            iCalendar Event object.
        """
        vevent = ICalEvent()

        # UID
        vevent.add("uid", event.uid)

        # DTSTART and DTEND
        if event.all_day:
            # All-day events use DATE format
            vevent.add("dtstart", event.date_start.date())
            vevent.add("dtend", event.date_end.date())
        else:
            # Regular events use datetime format
            vevent.add("dtstart", event.date_start)
            vevent.add("dtend", event.date_end)

        # SUMMARY (title)
        if event.title:
            vevent.add("summary", event.title)

        # DESCRIPTION
        if event.description:
            vevent.add("description", event.description)

        # RRULE (recurrence rule)
        if event.rrule:
            vevent.add("rrule", event.rrule)

        # RDATE (additional recurrence dates)
        if event.rdate:
            for rdate in event.rdate:
                vevent.add("rdate", rdate)

        # EXDATE (exception dates)
        if event.exdate:
            for exdate in event.exdate:
                vevent.add("exdate", exdate)

        # DTSTAMP (timestamp when event was created/modified)
        vevent.add("dtstamp", datetime.now(UTC))

        return vevent

