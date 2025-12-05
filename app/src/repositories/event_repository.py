"""
EventRepository implementation for Event entity.

Provides CRUD operations and query methods for Event model.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.event import Event
from repositories.exceptions import EventNotFoundError
from repositories.schemas import NOT_SET, EventCreateSchema, EventFilter, EventResponse, EventUpdateSchema


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

        if filter.start_date_from is not NOT_SET:
            stmt = stmt.where(Event.date_start >= filter.start_date_from)
        if filter.start_date_to is not NOT_SET:
            stmt = stmt.where(Event.date_start <= filter.start_date_to)

        # Ordering (by date_start, then by id for stability)
        stmt = stmt.order_by(Event.date_start, Event.id)

        result = await self.session.execute(stmt)
        return [EventResponse.from_model(event) for event in result.scalars().all()]
