"""
EventRepository implementation for Event entity.

Provides CRUD operations and query methods for Event model.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.event import Event
from repositories.base_repository import BaseRepository
from repositories.exceptions import EventNotFoundError
from repositories.schemas import EventCreateSchema, EventFilter, EventResponse, EventUpdateSchema

# TODO: Validation and exeptions


class EventRepository(BaseRepository[EventResponse]):
    """Repository for Event entity operations.

    Provides methods for creating, reading, updating, and deleting events,
    as well as querying events with various filters.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize EventRepository with a database session.

        Args:
            session: SQLAlchemy async session to use for database operations.
        """
        super().__init__(session)

    async def get_by_id(self, entity_id: int) -> EventResponse | None:
        """Retrieve an event by its ID.

        Args:
            entity_id: The ID of the event to retrieve.

        Returns:
            The event response if found, None otherwise.
        """
        result = await self.session.get(Event, entity_id)
        if result is None:
            return None
        return EventResponse.from_model(result)

    async def create(self, data: list[EventCreateSchema], *args, **kwargs) -> list[EventResponse]:
        """Create a new event.

        If reminder_offset is not provided, uses default from user settings.
        If need_to_remind is True, automatically creates a corresponding Reminder.

        Args:
            data: list of EventCreateSchema with event data.

        Returns:
            The created events list as responses.
        """
        events = []
        for item in data:
            event = Event(
                user_id=item.user_id,
                uid=item.uid,
                calendar_id=item.calendar_id,
                date_start=item.date_start,
                date_end=item.date_end,
                all_day=item.all_day,
                need_to_remind=item.need_to_remind,
                rrule=item.rrule,
                rdate=item.rdate,
                exdate=item.exdate,
                title=item.title,
                description=item.description,
            )
            self.session.add(event)
            await self.session.flush()
            await self.session.refresh(event)
            events.append(EventResponse.from_model(event))
        return events

    async def update(self, event_id: int, data: EventUpdateSchema, *args, **kwargs) -> EventResponse:
        """Update an existing event.

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

        # Update only provided fields
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(event_model, key, value)
        await self.session.flush()

        await self.session.refresh(event_model)
        return EventResponse.from_model(event_model)

    async def delete(self, entity_id: int, *args, **kwargs) -> None:
        """Delete an event by ID.

        Args:
            entity_id: The ID of the event to delete.
        """
        event_model = await self.session.get(Event, entity_id)
        if event_model is None:
            raise EventNotFoundError(event_id=entity_id)

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
        if filter.uid is not None:
            stmt = stmt.where(Event.uid == filter.uid)
        if filter.user_id is not None:
            stmt = stmt.where(Event.user_id == filter.user_id)
        if filter.calendar_id is not None:
            stmt = stmt.where(Event.calendar_id == filter.calendar_id)
        if filter.start_date_from is not None:
            stmt = stmt.where(Event.date_start >= filter.start_date_from)
        if filter.start_date_to is not None:
            stmt = stmt.where(Event.date_start <= filter.start_date_to)

        # Ordering (by date_start, then by id for stability)
        stmt = stmt.order_by(Event.date_start, Event.id)

        # Pagination
        stmt = stmt.offset(filter.offset).limit(filter.limit)

        result = await self.session.execute(stmt)
        events = list(result.scalars().all())
        return [EventResponse.from_model(event) for event in events]
