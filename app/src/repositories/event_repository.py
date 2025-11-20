"""
EventRepository implementation for Event entity.

Provides CRUD operations and query methods for Event model.
"""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.event import Event
from models.settings import Settings
from repositories.base_repository import BaseRepository
from repositories.exceptions import EventNotFoundError
from repositories.schemas import EventCreateSchema, EventFilter, EventUpdateSchema


class EventRepository(BaseRepository[Event]):
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

    async def get_by_id(self, entity_id: int) -> Event | None:
        """Retrieve an event by its ID.

        Args:
            entity_id: The ID of the event to retrieve.

        Returns:
            The event if found, None otherwise.
        """
        result = await self.session.get(Event, entity_id)
        return result

    async def create(self, data: EventCreateSchema, *args, **kwargs) -> Event:
        """Create a new event.

        If reminder_offset is not provided, uses default from user settings.

        Args:
            data: EventCreateSchema with event data.

        Returns:
            The created event.

        Raises:
            EventValidationError: If validation fails.
        """
        # Get default reminder_offset if not provided
        reminder_offset = data.reminder_offset
        if reminder_offset is None:
            reminder_offset = await self._get_default_reminder_offset(data.user_id)

        # Create event
        event = Event(
            user_id=data.user_id,
            title=data.title,
            date_start=data.date_start,
            date_end=data.date_end,
            reminder_offset=reminder_offset,
            need_to_remind=data.need_to_remind,
            description=data.description,
            rrule=data.rrule,
            calendar_id=data.calendar_id,
        )

        self.session.add(event)
        await self.session.flush()
        await self.session.refresh(event)
        return event

    async def update(self, entity_id: int, data: EventUpdateSchema, *args, **kwargs) -> Event:
        """Update an existing event.

        Only provided fields will be updated. Other fields remain unchanged.

        Args:
            entity_id: The ID of the event to update.
            data: EventUpdateSchema with fields to update.

        Returns:
            The updated event.

        Raises:
            EventNotFoundError: If the event is not found.
        """
        event = await self.get_by_id(entity_id)
        if event is None:
            raise EventNotFoundError(event_id=entity_id)

        # Update only provided fields
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(event, key, value)

        await self.session.flush()
        await self.session.refresh(event)
        return event

    async def delete(self, entity_id: int, user_id: int | None = None, *args, **kwargs) -> None:
        """Delete an event by ID.

        Optionally checks that the event belongs to the specified user.

        Args:
            entity_id: The ID of the event to delete.
            user_id: Optional user ID to verify ownership.

        Raises:
            EventNotFoundError: If the event is not found or doesn't belong to user.
        """
        event = await self.get_by_id(entity_id)
        if event is None:
            raise EventNotFoundError(event_id=entity_id)

        if user_id is not None and event.user_id != user_id:
            raise EventNotFoundError(event_id=entity_id, user_id=user_id)

        await self.session.delete(event)
        await self.session.flush()

    async def get_by_user_id(self, user_id: int) -> list[Event]:
        """Retrieve all events for a specific user.

        Args:
            user_id: The user ID to filter events by.

        Returns:
            List of events for the user, ordered by date_start.
        """
        stmt = select(Event).where(Event.user_id == user_id).order_by(Event.date_start)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def find(self, filter: EventFilter) -> list[Event]:
        """Find events matching the provided filter.

        Args:
            filter: EventFilter with filtering criteria.

        Returns:
            List of matching events, ordered by date_start.
        """
        stmt = select(Event)

        # Apply filters
        if filter.user_id is not None:
            stmt = stmt.where(Event.user_id == filter.user_id)
        if filter.calendar_id is not None:
            stmt = stmt.where(Event.calendar_id == filter.calendar_id)
        if filter.start_date_from is not None:
            stmt = stmt.where(Event.date_start >= filter.start_date_from)
        if filter.start_date_to is not None:
            stmt = stmt.where(Event.date_start <= filter.start_date_to)
        if filter.need_to_remind is not None:
            stmt = stmt.where(Event.need_to_remind == filter.need_to_remind)

        # Ordering (by date_start, then by id for stability)
        stmt = stmt.order_by(Event.date_start, Event.id)

        # Pagination
        stmt = stmt.offset(filter.offset).limit(filter.limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_upcoming_for_reminders(self, user_id: int, limit: int = 10) -> list[Event]:
        """Get upcoming events that need reminders.

        Returns events that:
        - Belong to the specified user
        - Have need_to_remind=True
        - Have date_start in the future

        Args:
            user_id: The user ID to filter events by.
            limit: Maximum number of events to return.

        Returns:
            List of upcoming events that need reminders, ordered by date_start.
        """
        now = datetime.now(UTC)
        stmt = (
            select(Event)
            .where(Event.user_id == user_id)
            .where(Event.need_to_remind == True)  # noqa: E712
            .where(Event.date_start > now)
            .order_by(Event.date_start)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def _get_default_reminder_offset(self, user_id: int) -> int:
        """Get default reminder offset from user settings.

        Args:
            user_id: The user ID to get settings for.

        Returns:
            Default reminder offset in seconds, or 15 minutes if not found.
        """
        stmt = select(Settings).where(Settings.user_id == user_id)
        result = await self.session.execute(stmt)
        settings = result.scalar_one_or_none()

        if settings and settings.default_reminder_offset:
            return settings.default_reminder_offset
        return 15 * 60  # fallback: 15 minutes
