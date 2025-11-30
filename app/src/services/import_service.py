"""Import service for importing events from icalendar files."""

import uuid
from datetime import date, datetime, time, timedelta

from pydantic import BaseModel, Field

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


class ExternalCalendarInfo(BaseModel):
    """Information about external calendar."""

    name: str = Field(..., description="Name of the external calendar.")
    url: str | None = Field(None, description="URL of the external calendar.")


class ImportService:
    """Import service for importing events from icalendar files."""

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

    async def _create_local_calendar(self, user_id: int, entities: list[tuple[Event, list[Reminder]]]):
        calendar_repo = self.store.get_calendar_repository
        event_repo = self.store.get_event_repository
        reminder_repo = self.store.get_reminder_repository

        calendar = await calendar_repo.create([CalendarCreateSchema(user_id=user_id, name="local calendar", url=None)])
        calendar = calendar[0]
        for entity in entities:
            event = entity[0]
            reminders = entity[1]
            event = await event_repo.create(
                [
                    EventCreateSchema(
                        user_id=user_id,
                        calendar_id=calendar.id,
                        uid=event.uid if event.uid is not None else await self._generate_uid(),
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
                ]
            )
            event = event[0]
            for reminder in reminders:
                await reminder_repo.create(
                    [
                        ReminderCreateSchema(
                            event_id=event.id,
                            description=reminder.description,
                            trigger_offset=reminder.trigger_offset,
                            trigger_datetime=reminder.trigger_datetime,
                            repeat_count=reminder.repeat_count,
                            repeat_interval=reminder.repeat_interval,
                        )
                    ]
                )

    async def _update_local_calendar(self, calendar: Calendar, entities: list[tuple[Event, list[Reminder]]]):
        event_repo = self.store.get_event_repository
        reminder_repo = self.store.get_reminder_repository

        for entity in entities:
            new_event = entity[0]
            new_reminders = entity[1]
            filter = EventFilter(uid=new_event.uid)  # type: ignore[call-arg]
            old_event = await event_repo.find(filter)
            if old_event == []:
                # creating event if it does not exist
                new_event = await event_repo.create(
                    [
                        EventCreateSchema(
                            user_id=calendar.user_id,
                            calendar_id=calendar.id,
                            uid=new_event.uid if new_event.uid is not None else await self._generate_uid(),
                            date_start=new_event.date_start,
                            date_end=new_event.date_end,
                            all_day=self._is_all_day(new_event.date_start, new_event.date_end),
                            need_to_remind=True,
                            rrule=new_event.rrule,
                            rdate=new_event.rdate,
                            exdate=new_event.exdate,
                            title=new_event.title,
                            description=new_event.description,
                        )
                    ]
                )
                new_event = new_event[0]
            else:
                # updating event
                await event_repo.update(
                    old_event[0].id,
                    EventUpdateSchema(
                        date_start=new_event.date_start,
                        date_end=new_event.date_end,
                        all_day=self._is_all_day(new_event.date_start, new_event.date_end),
                        need_to_remind=True,
                        rrule=new_event.rrule,
                        rdate=new_event.rdate,
                        exdate=new_event.exdate,
                        title=new_event.title,
                        description=new_event.description,
                    ),
                )
                # deleting reminders
                old_reminders = await reminder_repo.find(old_event[0].id)
                if old_reminders is not None:
                    for reminder in old_reminders:
                        await reminder_repo.delete(reminder.id)

            event_id = old_event[0].id if old_event != [] else new_event.id
            # creating reminders
            for reminder in new_reminders:
                await reminder_repo.create(
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
    ):
        calendar_repo = self.store.get_calendar_repository
        event_repo = self.store.get_event_repository

        calendar = await calendar_repo.create(
            [CalendarCreateSchema(user_id=user_id, name=calendar_name, url=calendar_url)]
        )
        calendar = calendar[0]
        for entity in entities:
            event = entity[0]
            # reminders = entity[1]
            # reminders are not importing from external calendars in this version
            event = await event_repo.create(
                [
                    EventCreateSchema(
                        user_id=user_id,
                        calendar_id=calendar.id,
                        uid=event.uid if event.uid is not None else await self._generate_uid(),
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
                ]
            )

    async def _update_external_calendar(self, calendar: Calendar, entities: list[tuple[Event, list[Reminder]]]):
        event_repo = self.store.get_event_repository

        # deleting events
        events = await event_repo.find(EventFilter(calendar_id=calendar.id))  # type: ignore[call-arg]
        if events != []:
            for event in events:
                await event_repo.delete(event.id)

        # creating events
        for entity in entities:
            event = entity[0]
            # reminders are not importing from external calendars in this version
            event = await event_repo.create(
                [
                    EventCreateSchema(
                        user_id=calendar.user_id,
                        calendar_id=calendar.id,
                        uid=event.uid if event.uid is not None else await self._generate_uid(),
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
                ]
            )

    async def _generate_uid(self) -> str:
        event_repo = self.store.get_event_repository
        # generate unique id for event or reminder and check if it does not exist in the database
        for _ in range(1000):
            uid = str(uuid.uuid4())
            if not await event_repo.find(EventFilter(uid=uid)):  # type: ignore[call-arg]
                return uid
        raise ValueError("Failed to generate unique ID for event or reminder")

    def _is_all_day(self, dtstart, dtend):
        if isinstance(dtstart, date) and not isinstance(dtstart, datetime):
            return True
        if isinstance(dtstart, datetime) and isinstance(dtend, datetime):
            # check full-day alignment
            return (
                dtstart.time() == time(0, 0)
                and dtend.time() == time(0, 0)
                and (dtend - dtstart) % timedelta(days=1) == timedelta(0)
            )
        return False
