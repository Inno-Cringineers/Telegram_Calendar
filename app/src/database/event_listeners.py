"""
SQLAlchemy event listeners for triggering scheduler rebuilds after database commits.

This module sets up event listeners that monitor database changes and trigger
scheduler rebuilds after successful commits. This ensures that rebuild_user_schedule
is called only after data is actually persisted to the database.
"""

from typing import TYPE_CHECKING

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession

from logger.logger import logger

if TYPE_CHECKING:
    from models.event import Event
    from models.reminder import Reminder
    from models.settings import Settings


def setup_event_listeners() -> None:
    """Register all event listeners for database changes.

    This function should be called once during application initialization,
    after the session maker is created but before any database operations.
    """
    # Track changes before flush to capture information before objects are removed from session
    @event.listens_for(AsyncSession, "before_flush")
    def on_before_flush(session: AsyncSession, flush_context: object, instances: object) -> None:
        """Track changes before flush to save user IDs for deleted objects.

        Args:
            session: The SQLAlchemy async session.
            flush_context: Flush context (unused).
            instances: Instances being flushed (unused).
        """
        # Initialize tracking sets in session.info if not present
        if "scheduler_rebuild_users" not in session.info:
            session.info["scheduler_rebuild_users"] = {
                "daily_plan": set(),
                "reminder": set(),
            }

        daily_plan_users = session.info["scheduler_rebuild_users"]["daily_plan"]
        reminder_users = session.info["scheduler_rebuild_users"]["reminder"]

        # Process new objects (inserted)
        for obj in session.new:
            if _is_settings(obj):
                settings = obj
                # New settings always trigger rebuild for both schedulers
                daily_plan_users.add(settings.user_id)
                reminder_users.add(settings.user_id)
            elif _is_event(obj):
                event_obj = obj
                reminder_users.add(event_obj.user_id)
            elif _is_reminder(obj):
                reminder = obj
                # Need to get user_id from event
                if reminder.event is not None:
                    reminder_users.add(reminder.event.user_id)
                else:
                    # If event is not loaded, save event_id to query later in after_commit
                    if "updated_reminder_event_ids" not in session.info:
                        session.info["updated_reminder_event_ids"] = []
                    session.info["updated_reminder_event_ids"].append(reminder.event_id)
                else:
                    # If event is not loaded, save event_id to query later in after_commit
                    if "new_reminder_event_ids" not in session.info:
                        session.info["new_reminder_event_ids"] = []
                    session.info["new_reminder_event_ids"].append(reminder.event_id)

        # Process dirty objects (updated)
        for obj in session.dirty:
            if _is_settings(obj):
                settings = obj
                # Check if daily_plans_enabled or daily_plans_time changed
                # Use inspect to get attribute history
                from sqlalchemy import inspect

                insp = inspect(obj)
                attrs = insp.attrs
                if "daily_plans_enabled" in attrs:
                    hist = attrs["daily_plans_enabled"].history
                    if hist.has_changes():
                        daily_plan_users.add(settings.user_id)
                if "daily_plans_time" in attrs:
                    hist = attrs["daily_plans_time"].history
                    if hist.has_changes():
                        daily_plan_users.add(settings.user_id)
                # Also trigger reminder scheduler for settings changes
                reminder_users.add(settings.user_id)
            elif _is_event(obj):
                event_obj = obj
                reminder_users.add(event_obj.user_id)
            elif _is_reminder(obj):
                reminder = obj
                # Need to get user_id from event
                if reminder.event is not None:
                    reminder_users.add(reminder.event.user_id)
                else:
                    # If event is not loaded, save event_id to query later in after_commit
                    if "updated_reminder_event_ids" not in session.info:
                        session.info["updated_reminder_event_ids"] = []
                    session.info["updated_reminder_event_ids"].append(reminder.event_id)

        # Process deleted objects - save user_id before deletion
        for obj in session.deleted:
            if _is_settings(obj):
                settings = obj
                daily_plan_users.add(settings.user_id)
                reminder_users.add(settings.user_id)
            elif _is_event(obj):
                event_obj = obj
                reminder_users.add(event_obj.user_id)
            elif _is_reminder(obj):
                reminder = obj
                # For deleted reminders, try to get user_id from event
                # If event is not loaded, save event_id to query later
                if reminder.event is not None:
                    reminder_users.add(reminder.event.user_id)
                else:
                    # Store event_id to query later in after_commit
                    if "deleted_reminder_event_ids" not in session.info:
                        session.info["deleted_reminder_event_ids"] = []
                    session.info["deleted_reminder_event_ids"].append(reminder.event_id)

    # Register after_commit listener for AsyncSession
    @event.listens_for(AsyncSession, "after_commit")
    async def on_after_commit(session: AsyncSession) -> None:
        """Handle after_commit event to trigger scheduler rebuilds.

        Args:
            session: The SQLAlchemy async session that just committed.
        """
        try:
            # Get tracked user IDs from session.info
            daily_plan_users: set[int] = session.info.get("scheduler_rebuild_users", {}).get(
                "daily_plan", set()
            )
            reminder_users: set[int] = session.info.get("scheduler_rebuild_users", {}).get(
                "reminder", set()
            )

            # Handle reminders that didn't have event loaded (new, updated, or deleted)
            all_reminder_event_ids: list[int] = []
            all_reminder_event_ids.extend(session.info.get("new_reminder_event_ids", []))
            all_reminder_event_ids.extend(session.info.get("updated_reminder_event_ids", []))
            all_reminder_event_ids.extend(session.info.get("deleted_reminder_event_ids", []))

            if all_reminder_event_ids:
                # Query user_id for reminders using event_id
                from sqlalchemy import select

                from models.event import Event

                # Query user_id for events associated with reminders
                result = await session.execute(
                    select(Event.user_id).where(Event.id.in_(all_reminder_event_ids))
                )
                user_ids = result.scalars().all()
                reminder_users.update(user_ids)

            # Trigger rebuilds for daily plan scheduler
            if daily_plan_users:
                from services.daily_plan_scheduler import get_daily_plan_scheduler

                try:
                    scheduler = get_daily_plan_scheduler()
                    for user_id in daily_plan_users:
                        await scheduler.rebuild_user_schedule(user_id)
                        logger.debug(
                            "Daily plan scheduler: triggered rebuild for user %s after commit", user_id
                        )
                except RuntimeError:
                    # Scheduler not initialized yet, skip
                    pass

            # Trigger rebuilds for reminder scheduler
            if reminder_users:
                from services.reminder_scheduler import get_reminder_scheduler

                try:
                    scheduler = get_reminder_scheduler()
                    for user_id in reminder_users:
                        await scheduler.rebuild_user_schedule(user_id)
                        logger.debug(
                            "Reminder scheduler: triggered rebuild for user %s after commit", user_id
                        )
                except RuntimeError:
                    # Scheduler not initialized yet, skip
                    pass

            # Clean up session.info
            session.info.pop("scheduler_rebuild_users", None)
            session.info.pop("new_reminder_event_ids", None)
            session.info.pop("updated_reminder_event_ids", None)
            session.info.pop("deleted_reminder_event_ids", None)

        except Exception as e:
            logger.error("Error in after_commit event listener: %s", e, exc_info=True)


def _is_settings(obj: object) -> bool:
    """Check if object is a Settings instance.

    Args:
        obj: Object to check.

    Returns:
        True if object is a Settings instance, False otherwise.
    """
    # Use string comparison to avoid circular imports
    return obj.__class__.__name__ == "Settings"


def _is_event(obj: object) -> bool:
    """Check if object is an Event instance.

    Args:
        obj: Object to check.

    Returns:
        True if object is an Event instance, False otherwise.
    """
    return obj.__class__.__name__ == "Event"


def _is_reminder(obj: object) -> bool:
    """Check if object is a Reminder instance.

    Args:
        obj: Object to check.

    Returns:
        True if object is a Reminder instance, False otherwise.
    """
    return obj.__class__.__name__ == "Reminder"

