"""
Store pattern implementation for managing all repositories and services.

The Store provides a single entry point for all data access operations,
simplifying initialization and configuration.

Architecture:
    Handler → Store(session) → Repositories(session) + Services(store)

All components use the same session, ensuring transactional consistency.
UnitOfWork manages the session lifecycle (create, commit, rollback, close).
"""

from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from repositories.calendar_repository import CalendarRepository
    from repositories.event_repository import EventRepository
    from repositories.reminder_repository import ReminderRepository
    from repositories.settings_repository import SettingsRepository
    # from services.event_service import EventService


class Store:
    """Store that aggregates all repositories and services.

    All repositories and services use the same session from UnitOfWork,
    ensuring all operations are in a single transaction.

    Usage:
        async def handler(message: Message, data: dict):
            store: Store = data["store"]  # From StoreMiddleware

            # Use repositories directly
            calendar = await store.calendars.create(...)
            event = await store.events.create(...)
            reminder = await store.reminders.create(...)
            settings = await store.settings.create(...)

            # Or use services (which use repositories through Store)
            # event = await store.event_service.create_with_reminder(...)
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize Store with a database session.

        Args:
            session: SQLAlchemy async session from UnitOfWork.
                    All repositories and services will use this session.
        """
        self.session = session
        # Repositories are initialized lazily to avoid circular imports
        self._calendar_repository: CalendarRepository | None = None
        self._event_repository: EventRepository | None = None
        self._reminder_repository: ReminderRepository | None = None
        self._settings_repository: SettingsRepository | None = None
        # Services will be initialized here when implemented
        # self._event_service: "EventService | None" = None

    # ========================================================================
    # REPOSITORIES
    # ========================================================================

    @property
    def get_calendar_repository(self) -> "CalendarRepository":
        """Get CalendarRepository instance.

        Returns:
            CalendarRepository: The calendar repository instance using Store's session.
        """
        if self._calendar_repository is None:
            from repositories.calendar_repository import CalendarRepository

            self._calendar_repository = CalendarRepository(self.session)
        return self._calendar_repository

    @property
    def get_event_repository(self) -> "EventRepository":
        """Get EventRepository instance.

        Returns:
            EventRepository: The event repository instance using Store's session.
        """
        if self._event_repository is None:
            from repositories.event_repository import EventRepository

            self._event_repository = EventRepository(self.session)
        return self._event_repository

    @property
    def get_reminder_repository(self) -> "ReminderRepository":
        """Get ReminderRepository instance.

        Returns:
            ReminderRepository: The reminder repository instance using Store's session.
        """
        if self._reminder_repository is None:
            from repositories.reminder_repository import ReminderRepository

            self._reminder_repository = ReminderRepository(self.session)
        return self._reminder_repository

    @property
    def get_settings_repository(self) -> "SettingsRepository":
        """Get SettingsRepository instance.

        Returns:
            SettingsRepository: The settings repository instance using Store's session.
        """
        if self._settings_repository is None:
            from repositories.settings_repository import SettingsRepository

            self._settings_repository = SettingsRepository(self.session)
        return self._settings_repository

    # ========================================================================
    # SERVICES (when implemented)
    # ========================================================================

    # @property
    # def event_service(self) -> "EventService":
    #     """Get EventService instance.
    #
    #     Services receive Store instance, giving them access to all repositories.
    #
    #     Returns:
    #         EventService: The event service instance.
    #     """
    #     if self._event_service is None:
    #         from services.event_service import EventService
    #         self._event_service = EventService(self)  # Pass Store, not session
    #     return self._event_service
