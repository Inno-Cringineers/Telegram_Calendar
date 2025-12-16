"""
ReminderRepository implementation for Reminder entity.

Provides CRUD operations and query methods for Reminder model.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.event import Event
from models.reminder import Reminder
from repositories.exceptions import ReminderNotFoundError
from repositories.schemas import NOT_SET, ReminderCreateSchema, ReminderFilter, ReminderResponse, ReminderUpdateSchema


def _normalize_trigger_offset(trigger_offset: str) -> str:
    """Normalize trigger_offset to ensure it's negative (before event).

    Args:
        trigger_offset: RFC 5545 trigger offset string.

    Returns:
        Normalized trigger offset string with negative sign.

    Raises:
        ValueError: If trigger_offset is empty or invalid.
    """
    if not trigger_offset:
        raise ValueError("trigger_offset cannot be empty")
    if not trigger_offset.startswith("-"):
        trigger_offset = "-" + trigger_offset
    return trigger_offset


class ReminderRepository:
    def __init__(self, session: AsyncSession) -> None:
        """Initialize SettingsRepository with a database session.

        Args:
            session: SQLAlchemy async session to use for database operations.
        """
        self.session = session

    async def get_by_id(self, reminder_id: int) -> ReminderResponse | None:
        """Retrieve a reminder by its ID.

        Args:
            reminder_id: The ID of the reminder to retrieve.

        Returns:
            The reminder response if found, None otherwise.
        """
        result = await self.session.get(Reminder, reminder_id)
        if result is None:
            return None
        return ReminderResponse.from_model(result)

    async def create_one(self, data: ReminderCreateSchema) -> ReminderResponse:
        """Create a new reminders.

        Args:
            data: ReminderCreateSchema with reminder data.

        Returns:
            The created reminder as response.

        Raises:
            ValueError: If trigger_offset is invalid.
        """
        # Нормализуем trigger_offset: убеждаемся, что он отрицательный
        normalized_offset = _normalize_trigger_offset(data.trigger_offset)
        reminder = Reminder(
            event_id=data.event_id,
            description=data.description,
            trigger_offset=normalized_offset,
        )
        self.session.add(reminder)
        await self.session.flush()
        await self.session.refresh(reminder)
        return ReminderResponse.from_model(reminder)

    async def create_many(self, data: list[ReminderCreateSchema]) -> list[ReminderResponse]:
        """Create multiple reminders.

        Args:
            data: list of ReminderCreateSchema with reminder data.

        Returns:
            The created reminders as responses.

        Raises:
            ValueError: If trigger_offset is invalid for any reminder.
        """
        reminders = []
        for item in data:
            # Нормализуем trigger_offset: убеждаемся, что он отрицательный
            normalized_offset = _normalize_trigger_offset(item.trigger_offset)
            reminder = Reminder(
                event_id=item.event_id,
                description=item.description,
                trigger_offset=normalized_offset,
            )
            self.session.add(reminder)
            await self.session.flush()
            await self.session.refresh(reminder)
            reminders.append(ReminderResponse.from_model(reminder))
        return reminders

    async def update_by_id(self, reminder_id: int, data: ReminderUpdateSchema) -> ReminderResponse:
        """Update an existing reminder.

        Args:
            reminder_id: The ID of the reminder to update.
            data: ReminderUpdateSchema with fields to update.

        Returns:
            Updated reminder response.
        """
        reminder_model = await self.session.get(Reminder, reminder_id)
        if reminder_model is None:
            raise ReminderNotFoundError(reminder_id=reminder_id)

        return await self._update_model(reminder_model, data)

    async def _update_model(self, reminder_model: Reminder, data: ReminderUpdateSchema) -> ReminderResponse:
        """Update reminder model with data from schema.

        Args:
            reminder_model: Reminder model to update.
            data: ReminderUpdateSchema with fields to update.

        Returns:
            Updated reminder response.

        Raises:
            ValueError: If trigger_offset is invalid.
        """
        for field in data.__dataclass_fields__:
            value = getattr(data, field)
            if value is not NOT_SET:
                # Нормализуем trigger_offset, если он обновляется
                if field == "trigger_offset":
                    value = _normalize_trigger_offset(value)
                setattr(reminder_model, field, value)

        await self.session.flush()
        await self.session.refresh(reminder_model)
        return ReminderResponse.from_model(reminder_model)

    async def find(self, filter: ReminderFilter) -> list[ReminderResponse]:
        """Find reminders matching the provided filter.

        Args:
            filter: ReminderFilter with filtering criteria.

        Returns:
            The list of reminders as responses if found, empty list otherwise.
        """
        if filter.user_id is not NOT_SET:
            # Filter by user_id requires join with Event table
            stmt = select(Reminder).join(Event).where(Event.user_id == filter.user_id)
        else:
            stmt = select(Reminder)

        conditions = [
            getattr(Reminder, field) == value
            for field, value in vars(filter).items()
            if value is not NOT_SET and field != "user_id"
        ]

        if conditions:
            stmt = stmt.where(*conditions)

        result = await self.session.execute(stmt)
        return [ReminderResponse.from_model(reminder) for reminder in result.scalars().all()]

    async def delete_by_id(self, reminder_id: int) -> None:
        """Delete a reminder by ID.

        Args:
            reminder_id: The ID of the reminder to delete.
        """
        reminder_model = await self.session.get(Reminder, reminder_id)
        if reminder_model is None:
            raise ReminderNotFoundError(reminder_id=reminder_id)
        await self.session.delete(reminder_model)
        await self.session.flush()

    async def delete_by_description_and_user_id(self, description: str, user_id: int) -> None:
        """Delete reminders by description and user_id.

        Args:
            description: The description to match.
            user_id: The user ID to filter by.
        """
        stmt = select(Reminder).join(Event).where(Event.user_id == user_id, Reminder.description == description)
        result = await self.session.execute(stmt)
        reminders = result.scalars().all()
        for reminder in reminders:
            await self.session.delete(reminder)
        await self.session.flush()
