"""
EventRepository implementation for Event entity.

Provides CRUD operations and query methods for Event model.
"""

from collections.abc import Iterable
from datetime import datetime

from dateutil.rrule import rrulestr
from icalendar import Event as ICalEvent
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.event import Event
from repositories.exceptions import EventNotFoundError
from repositories.schemas import (
    NOT_SET,
    EventCreateSchema,
    EventDurationFilter,
    EventFilter,
    EventResponse,
    EventUpdateSchema,
)


class EventRepository:
    """Repository for Event entity operations.

    Provides methods for creating, reading, updating, and deleting events,
    as well as querying events with various filters.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize EventRepository with a database session.

        Args:
            session: SQLAlchemy async session to use for database operations.
        """
        self.session = session

    async def get_by_id(self, event_id: int) -> EventResponse | None:
        """Retrieve an event by its ID.

        Args:
            event_id: The ID of the event to retrieve.

        Returns:
            The event response if found, None otherwise.
        """
        result = await self.session.get(Event, event_id)
        if result is None:
            return None
        return EventResponse.from_model(result)

    async def create_one(self, data: EventCreateSchema) -> EventResponse:
        """Create a new event.

        If reminder_offset is not provided, uses default from user settings.
        If need_to_remind is True, automatically creates a corresponding Reminder.

        Args:
            data: EventCreateSchema with event data.

        Returns:
            The created event as response.
        """
        event = Event(
            user_id=data.user_id,
            uid=data.uid,
            calendar_id=data.calendar_id,
            date_start=data.date_start,
            date_end=data.date_end,
            all_day=data.all_day,
            need_to_remind=data.need_to_remind,
            rrule=data.rrule,
            rdate=data.rdate,
            exdate=data.exdate,
            title=data.title,
            description=data.description,
        )
        self.session.add(event)
        await self.session.flush()
        await self.session.refresh(event)
        return EventResponse.from_model(event)

    async def create_many(self, data: list[EventCreateSchema]) -> list[EventResponse]:
        """Create multiple events.

        Args:
            data: list of EventCreateSchema with event data.

        Returns:
            The created events as responses.
        """
        events = []
        for item in data:
            event = Event(
                user_id=item.user_id,
                uid=item.uid,
                calendar_id=item.calendar_id,
            )
            self.session.add(event)
            await self.session.flush()
            await self.session.refresh(event)
            events.append(EventResponse.from_model(event))
        return [EventResponse.from_model(event) for event in events]

    async def update_by_id(self, event_id: int, data: EventUpdateSchema) -> EventResponse:
        """Update an existing event by ID.

        Only provided fields will be updated. Other fields remain unchanged.

        Args:
            event_id: The ID of the event to update.
            data: EventUpdateSchema with fields to update.

        Returns:
            The updated event response.

        Raises:
            EventNotFoundError: If the event is not found.
        """
        event_model = await self.session.get(Event, event_id)
        if event_model is None:
            raise EventNotFoundError(event_id=event_id)

        return await self._update_model(event_model, data)

    async def _update_model(self, event_model: Event, data: EventUpdateSchema) -> EventResponse:
        for field in data.__dataclass_fields__:
            value = getattr(data, field)
            if value is not NOT_SET:
                setattr(event_model, field, value)

        await self.session.flush()
        await self.session.refresh(event_model)
        return EventResponse.from_model(event_model)

    async def delete_by_id(self, event_id: int) -> None:
        """Delete an event by ID.

        Args:
            event_id: The ID of the event to delete.
        """
        event_model = await self.session.get(Event, event_id)
        if event_model is None:
            raise EventNotFoundError(event_id=event_id)

        await self.session.delete(event_model)
        await self.session.flush()

    async def find(self, filter: EventFilter) -> list[EventResponse]:
        """Find events matching the provided filter.

        Args:
            filter: EventFilter with filtering criteria.

        Returns:
            List of matching events as responses, ordered by date_start.
        """
        stmt = select(Event)

        # Apply filters
        conditions = [getattr(Event, field) == value for field, value in vars(filter).items() if value is not NOT_SET]

        stmt = stmt.where(*conditions)

        # Ordering (by date_start, then by id for stability)
        stmt = stmt.order_by(Event.date_start, Event.id)

        result = await self.session.execute(stmt)
        return [EventResponse.from_model(event) for event in result.scalars().all()]

    async def find_by_duration(self, filter: EventDurationFilter) -> list[EventResponse]:
        """
        Find events that intersect with given duration [filter.duration_from, filter.duration_to].
        Handles RRULE, RDATE, EXDATE.
        """

        # Step 1: get all events for user (matching your domain logic)
        events = await self.find(EventFilter(user_id=filter.user_id))

        matched = []

        for event_resp in events:
            # Convert EventResponse back to model-like simple object
            # (или можно получить Event модель заново, если нужно)
            event_model = await self.session.get(Event, event_resp.id)

            for occ_start, occ_end in _event_occurrences(event_model, filter.duration_from, filter.duration_to):
                if _intersects(occ_start, occ_end, filter.duration_from, filter.duration_to):
                    matched.append(event_resp)
                    break  # event matches at least one occurrence — include only once

        return matched


def _event_occurrences(event: Event, from_dt: datetime, to_dt: datetime) -> Iterable[tuple[datetime, datetime]]:
    """
    Generate all occurrences (start, end) of event between from_dt and to_dt inclusive,
    taking into account RRULE, RDATE, and EXDATE.
    """

    duration = event.date_end - event.date_start

    # --------------------------------------
    # Build iCalendar VEVENT for recurrence
    # --------------------------------------
    vevent = ICalEvent()

    vevent.add("dtstart", event.date_start)
    vevent.add("dtend", event.date_end)

    if event.rrule:
        vevent.add("rrule", event.rrule)

    if event.rdate:
        for rd in event.rdate:
            vevent.add("rdate", rd)

    if event.exdate:
        for ex in event.exdate:
            vevent.add("exdate", ex)

    # 1) RRULE occurrences
    if event.rrule:
        rule = rrulestr(event.rrule, dtstart=event.date_start)
        for dt_start in rule.between(from_dt - duration, to_dt, inc=True):
            if event.exdate and dt_start in event.exdate:
                continue
            yield dt_start, dt_start + duration

    # 2) RDATE occurrences
    if event.rdate:
        for dt_start in event.rdate:
            if from_dt <= dt_start <= to_dt and (not event.exdate or dt_start not in event.exdate):
                yield dt_start, dt_start + duration

    # 3) Base event (single event)
    if event.rrule is None and not event.rdate:
        if not event.exdate:
            if not (event.date_end < from_dt or event.date_start > to_dt):
                yield event.date_start, event.date_end


def _intersects(start1, end1, start2, end2) -> bool:
    """Return True if two intervals intersect."""
    return not (end1 < start2 or end2 < start1)
