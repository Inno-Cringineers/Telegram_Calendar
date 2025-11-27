"""
ReminderRepository implementation for Reminder entity.

Provides CRUD operations and query methods for Reminder model.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.reminder import Reminder
from repositories.base_repository import BaseRepository
from repositories.exceptions import ReminderNotFoundError
from repositories.schemas import ReminderCreateSchema, ReminderUpdateSchema


class ReminderRepository(BaseRepository[Reminder]):
    def __init__(self, session: AsyncSession) -> None:
        """Initialize SettingsRepository with a database session.

        Args:
            session: SQLAlchemy async session to use for database operations.
        """
        super().__init__(session)

    async def get_by_id(self, entity_id: int) -> Reminder | None:
        """Retrieve a reminder by its ID.

        Args:
            entity_id: The ID of the reminder to retrieve.

        Returns:
            The reminder if found, None otherwise.
        """
        result = await self.session.get(Reminder, entity_id)
        return result

    async def create(self, data: list[ReminderCreateSchema], *args, **kwargs) -> list[Reminder]:
        """Create a new reminders.

        Args:
            data: list of ReminderCreateSchema with reminders data.
        """
        reminders = []
        for item in data:
            reminder = Reminder(
                event_id=item.event_id,
                description=item.description,
                trigger_offset=item.trigger_offset,
                trigger_datetime=item.trigger_datetime,
                repeat_count=item.repeat_count,
                repeat_interval=item.repeat_interval,
                sent=False,
            )
            self.session.add(reminder)
            await self.session.flush()
            reminders.append(reminder)
        return reminders

    async def update(self, entity_id: int, data: ReminderUpdateSchema, *args, **kwargs) -> Reminder:
        """Update an existing reminder.

        Args:
            entity_id: The ID of the reminder to update.
            data: ReminderUpdateSchema with fields to update.
        """
        reminder = await self.get_by_id(entity_id)
        if reminder is None:
            raise ReminderNotFoundError(reminder_id=entity_id)

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(reminder, key, value)

        await self.session.flush()
        await self.session.refresh(reminder)
        return reminder

    async def find(self, event_id: int) -> Reminder | None:
        """Find reminders by event ID.

        Args:
            event_id: The ID of the event to find reminders for.

        Returns:
            The reminder if found, None otherwise.
        """
        result = await self.session.execute(select(Reminder).where(Reminder.event_id == event_id))
        return result.scalar()

    async def delete(self, entity_id: int, *args, **kwargs) -> None:
        """Delete a reminder by ID.

        Args:
            entity_id: The ID of the reminder to delete.
        """
        reminder = await self.get_by_id(entity_id)
        if reminder is None:
            raise ReminderNotFoundError(reminder_id=entity_id)
        await self.session.delete(reminder)
        await self.session.flush()
