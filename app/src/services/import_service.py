"""Import service for importing events from icalendar files."""

import uuid

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
    url: str = Field(..., description="URL of the external calendar.")


class ImportService:
    """Import service for importing events from icalendar files."""

    def __init__(self, store: Store) -> None:
        """Initialize ImportService with a store.

        Args:
            store: Store to use repositories and services.
        """
        self.store = store

    async def import_calendar_from_file(
        self,
        file_path: str,
        user_id: int,
        external_calendar_info: ExternalCalendarInfo | None = None,
    ) -> None:
        """Import calendar from icalendar file.

        Args:
            file_path: Path to the icalendar file.
            user_id: Telegram user ID.
            external_calendar_info: Information about external calendar.
        """

        # loading entities from file using ICSParser
        entities = ICSParser(file_path).get_entities()

        calendar_repo = self.store.get_calendar_repository

        # check if calendar already exists
        if external_calendar_info is not None:
            filter = CalendarFilter(user_id=user_id, name=external_calendar_info.name)  # type: ignore[call-arg]
            calendar = await calendar_repo.find(filter)
            if calendar != []:
                await self._update_calendar(calendar[0], entities)
            else:
                await self._create_calendar(user_id, external_calendar_info, entities)
        else:
            await self._create_calendar(user_id, ExternalCalendarInfo(name="local calendar", url=""), entities)

    async def _create_calendar(
        self,
        user_id: int,
        external_calendar_info: ExternalCalendarInfo,
        entities: list[tuple[Event, list[Reminder]]],
    ) -> Calendar:
        calendar_repo = self.store.get_calendar_repository
        event_repo = self.store.get_event_repository
        reminder_repo = self.store.get_reminder_repository

        # creating calendar
        calendar = await calendar_repo.create(
            [
                CalendarCreateSchema(user_id=user_id, name=external_calendar_info.name, url=external_calendar_info.url),
            ]
        )
        calendar = calendar[0]

        # creating events and reminders
        for entity in entities:
            event = entity[0]
            reminders = entity[1]
            # creating event
            event = await event_repo.create(
                [
                    EventCreateSchema(
                        user_id=user_id,
                        calendar_id=calendar.id,
                        uid=event.uid if event.uid is not None else await self._generate_uid(),
                        date_start=event.date_start,
                        date_end=event.date_end,
                        all_day=True if event.date_start == event.date_end else False,
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

            # creating reminders
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

        return calendar

    async def _update_calendar(self, calendar: Calendar, entities: list[tuple[Event, list[Reminder]]]) -> Calendar:
        event_repo = self.store.get_event_repository
        reminder_repo = self.store.get_reminder_repository

        for entity in entities:
            new_event = entity[0]

            # find event by uid
            filter = EventFilter(uid=new_event.uid)  # type: ignore[call-arg]
            event = await event_repo.find(filter)
            if event == []:  # event not found
                # creating event
                event = await event_repo.create(
                    [
                        EventCreateSchema(
                            user_id=calendar.user_id,
                            calendar_id=calendar.id,
                            uid=new_event.uid if new_event.uid is not None else await self._generate_uid(),
                            date_start=new_event.date_start,
                            date_end=new_event.date_end,
                            all_day=True if new_event.date_start == new_event.date_end else False,
                            need_to_remind=True,
                            rrule=new_event.rrule,
                            rdate=new_event.rdate,
                            exdate=new_event.exdate,
                            title=new_event.title,
                            description=new_event.description,
                        )
                    ]
                )
            elif len(event) == 1:  # event found
                # updating event
                event = await event_repo.update(
                    event[0].id,
                    EventUpdateSchema(
                        date_start=new_event.date_start,
                        date_end=new_event.date_end,
                        all_day=True if new_event.date_start == new_event.date_end else False,
                        need_to_remind=True,
                        rrule=new_event.rrule,
                        rdate=new_event.rdate,
                        exdate=new_event.exdate,
                        title=new_event.title,
                        description=new_event.description,
                    ),
                )
            else:
                # multiple events found
                raise ValueError("Multiple events found for the same UID")

            # deleting reminders
            reminders = await reminder_repo.find(event.id)  # type: ignore[attr-defined]
            if reminders is not None:
                for reminder in reminders:
                    await reminder_repo.delete(reminder.id)

            # creating reminders
            for new_reminder in entity[1]:
                await reminder_repo.create(
                    [
                        ReminderCreateSchema(
                            event_id=event.id,  # type: ignore[attr-defined]
                            description=new_reminder.description,
                            trigger_offset=new_reminder.trigger_offset,
                            trigger_datetime=new_reminder.trigger_datetime,
                            repeat_count=new_reminder.repeat_count,
                            repeat_interval=new_reminder.repeat_interval,
                        )
                    ]
                )

        return calendar

    async def _generate_uid(self) -> str:
        event_repo = self.store.get_event_repository
        # generate unique id for event or reminder and check if it does not exist in the database
        for _ in range(1000):
            uid = str(uuid.uuid4())
            if not await event_repo.find(EventFilter(uid=uid)):  # type: ignore[call-arg]
                return uid
        raise ValueError("Failed to generate unique ID for event or reminder")
