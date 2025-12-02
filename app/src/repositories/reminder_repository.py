"""
ReminderRepository implementation for Reminder entity.

Provides CRUD operations and query methods for Reminder model.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.reminder import Reminder
from repositories.base_repository import BaseRepository
from repositories.exceptions import ReminderNotFoundError
from repositories.schemas import ReminderCreateSchema, ReminderResponse, ReminderUpdateSchema


class ReminderRepository(BaseRepository[ReminderResponse]):
    def __init__(self, session: AsyncSession) -> None:
        """Initialize SettingsRepository with a database session.

        Args:
            session: SQLAlchemy async session to use for database operations.
        """
        super().__init__(session)

    async def get_by_id(self, entity_id: int) -> ReminderResponse | None:
        """Retrieve a reminder by its ID.

        Args:
            entity_id: The ID of the reminder to retrieve.

        Returns:
            The reminder response if found, None otherwise.
        """
        result = await self.session.get(Reminder, entity_id)
        if result is None:
            return None
        return ReminderResponse.from_model(result)

    async def create(self, data: list[ReminderCreateSchema], *args, **kwargs) -> list[ReminderResponse]:
        """Create a new reminders.

        Args:
            data: list of ReminderCreateSchema with reminders data.

        Returns:
            Created reminders as responses.
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
            await self.session.refresh(reminder)
            reminders.append(ReminderResponse.from_model(reminder))
        return reminders

    async def update(self, entity_id: int, data: ReminderUpdateSchema, *args, **kwargs) -> ReminderResponse:
        """Update an existing reminder.

        Args:
            entity_id: The ID of the reminder to update.
            data: ReminderUpdateSchema with fields to update.

        Returns:
            Updated reminder response.
        """
        reminder_model = await self.session.get(Reminder, entity_id)
        if reminder_model is None:
            raise ReminderNotFoundError(reminder_id=entity_id)

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(reminder_model, key, value)

        await self.session.flush()
        await self.session.refresh(reminder_model)
        return ReminderResponse.from_model(reminder_model)

    async def find(self, event_id: int) -> list[ReminderResponse]:
        """Find reminders by event ID.

        Args:
            event_id: The ID of the event to find reminders for.

        Returns:
            The list of reminders as responses if found, empty list otherwise.
        """
        result = await self.session.execute(select(Reminder).where(Reminder.event_id == event_id))
        reminders = list(result.scalars().all())
        return [ReminderResponse.from_model(reminder) for reminder in reminders]

    async def delete(self, entity_id: int, *args, **kwargs) -> None:
        """Delete a reminder by ID.

        Args:
            entity_id: The ID of the reminder to delete.
        """
        reminder_model = await self.session.get(Reminder, entity_id)
        if reminder_model is None:
            raise ReminderNotFoundError(reminder_id=entity_id)
        await self.session.delete(reminder_model)
        await self.session.flush()
