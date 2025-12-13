"""
SQLAlchemy event listeners for triggering scheduler rebuilds after database commits.

This module sets up event listeners that monitor database changes and trigger
scheduler rebuilds after successful commits. This ensures that rebuild_user_schedule
is called only after data is actually persisted to the database.
"""

import asyncio
from typing import TYPE_CHECKING

from sqlalchemy import event
from sqlalchemy.orm import Session

from logger.logger import logger

if TYPE_CHECKING:
    pass  # pyright: ignore[reportUnusedImport]


def setup_event_listeners() -> None:
    """Register all event listeners for database changes.

    This function should be called once during application initialization,
    after the session maker is created but before any database operations.
    """
    logger.info("Setting up event listeners for scheduler rebuilds")

    # Track changes before flush to capture information before objects are removed from session
    # Use Session events which work for both sync and async sessions
    # For AsyncSession, events are triggered on the underlying sync_session
    @event.listens_for(Session, "before_flush")
    def on_before_flush(session: Session, flush_context: object, instances: object) -> None:  # pyright: ignore[reportUnusedFunction]
        """Track changes before flush to save user IDs for deleted objects.

        Args:
            session: The SQLAlchemy async session.
            flush_context: Flush context (unused).
            instances: Instances being flushed (unused).
        """
        # logger.debug(
        #     "Event listener: before_flush triggered, new=%s, dirty=%s, deleted=%s",
        #     len(session.new),
        #     len(session.dirty),
        #     len(session.deleted),
        # )

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
                    # If event is not loaded, try to load it synchronously
                    from models.event import Event

                    event = session.get(Event, reminder.event_id)
                    if event is not None:
                        reminder_users.add(event.user_id)
                    else:
                        logger.warning("Event listener: could not load event %s for reminder", reminder.event_id)

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
                    # If event is not loaded, try to load it synchronously
                    from models.event import Event

                    event = session.get(Event, reminder.event_id)
                    if event is not None:
                        reminder_users.add(event.user_id)
                    else:
                        logger.warning("Event listener: could not load event %s for reminder", reminder.event_id)

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
                # If event is not loaded, try to load it synchronously
                if reminder.event is not None:
                    reminder_users.add(reminder.event.user_id)
                else:
                    # Try to load event synchronously before deletion
                    from models.event import Event

                    event = session.get(Event, reminder.event_id)
                    if event is not None:
                        reminder_users.add(event.user_id)
                    else:
                        logger.warning(
                            "Event listener: could not load event %s for deleted reminder", reminder.event_id
                        )

        # logger.debug(
        #     "Event listener: before_flush completed, daily_plan_users=%s, reminder_users=%s",
        #     len(daily_plan_users),
        #     len(reminder_users),
        # )

    # Register after_commit listener
    # Use Session events which work for both sync and async sessions
    @event.listens_for(Session, "after_commit")
    def on_after_commit(session: Session) -> None:  # pyright: ignore[reportUnusedFunction]
        """Handle after_commit event to trigger scheduler rebuilds.

        Args:
            session: The SQLAlchemy session that just committed.
        """
        # logger.debug("Event listener: after_commit triggered, session type=%s", type(session).__name__)

        # Check if this session has sync_session attribute (indicates it's from AsyncSession)
        # AsyncSession wraps a sync Session, and events fire on the sync session
        # We need to check if we're in an async context
        try:
            # Get tracked user IDs from session.info
            scheduler_rebuild_users = session.info.get("scheduler_rebuild_users", {})
            daily_plan_users: set[int] = scheduler_rebuild_users.get("daily_plan", set())
            reminder_users: set[int] = scheduler_rebuild_users.get("reminder", set())

            # logger.debug(
            #     "Event listener: after_commit processing, daily_plan_users=%s, reminder_users=%s",
            #     len(daily_plan_users),
            #     len(reminder_users),
            # )

            # Schedule async work to run after commit
            async def _process_after_commit() -> None:
                """Process scheduler rebuilds asynchronously after commit."""

                # Trigger rebuilds for daily plan scheduler
                if daily_plan_users:
                    from services.daily_plan_scheduler import get_daily_plan_scheduler

                    try:
                        scheduler = get_daily_plan_scheduler()
                        for user_id in daily_plan_users:
                            await scheduler.rebuild_user_schedule(user_id)
                            # logger.debug("Daily plan scheduler: triggered rebuild for user %s after commit", user_id)
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
                            # logger.debug("Reminder scheduler: triggered rebuild for user %s after commit", user_id)
                    except RuntimeError:
                        # Scheduler not initialized yet, skip
                        pass

                # Clean up session.info (use the original session, not async_session)
                # Note: session is closed, but info should still be accessible
                session.info.pop("scheduler_rebuild_users", None)

            # Schedule the async work
            try:
                loop = asyncio.get_running_loop()
                # If loop is running, create a task
                # logger.debug("Event listener: creating task for async processing")
                asyncio.create_task(_process_after_commit())
            except RuntimeError:
                # No running loop, this shouldn't happen in async context
                logger.warning("Event listener: no running event loop found, trying to get event loop")
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(_process_after_commit())
                    else:
                        loop.run_until_complete(_process_after_commit())
                except RuntimeError:
                    logger.error("Event listener: failed to get event loop, cannot process async work")
                    # Try to run in new event loop as last resort
                    try:
                        asyncio.run(_process_after_commit())
                    except RuntimeError as e:
                        logger.error("Event listener: failed to run async work: %s", e)

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
