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
    from services.calendar_service import CalendarService
    from services.event_service import EventService
    from services.export_service import ExportService
    from services.import_service import ImportService
    from services.reminder_service import ReminderService
    from services.settings_service import SettingsService
    from services.upload_service import UploadService


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

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
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
        self._upload_service: UploadService | None = None
        self._import_service: ImportService | None = None
        self._export_service: ExportService | None = None
        self._settings_service: SettingsService | None = None
        self._calendar_service: CalendarService | None = None
        self._reminder_service: ReminderService | None = None
        self._event_service: EventService | None = None

    # ========================================================================
    # REPOSITORIES
    # ========================================================================

    @property
    def CalendarRepository(self) -> "CalendarRepository":
        """Get CalendarRepository instance.

        Returns:
            CalendarRepository: The calendar repository instance using Store's session.
        """
        if self._calendar_repository is None:
            from repositories.calendar_repository import CalendarRepository

            self._calendar_repository = CalendarRepository(self.session)
        return self._calendar_repository

    @property
    def EventRepository(self) -> "EventRepository":
        """Get EventRepository instance.

        Returns:
            EventRepository: The event repository instance using Store's session.
        """
        if self._event_repository is None:
            from repositories.event_repository import EventRepository

            self._event_repository = EventRepository(self.session)
        return self._event_repository

    @property
    def ReminderRepository(self) -> "ReminderRepository":
        """Get ReminderRepository instance.

        Returns:
            ReminderRepository: The reminder repository instance using Store's session.
        """
        if self._reminder_repository is None:
            from repositories.reminder_repository import ReminderRepository

            self._reminder_repository = ReminderRepository(self.session)
        return self._reminder_repository

    @property
    def SettingsRepository(self) -> "SettingsRepository":
        """Get SettingsRepository instance.

        Returns:
            SettingsRepository: The settings repository instance using Store's session.
        """
        if self._settings_repository is None:
            from repositories.settings_repository import SettingsRepository

            self._settings_repository = SettingsRepository(self.session)
        return self._settings_repository

    # ========================================================================
    # SERVICES
    # ========================================================================

    @property
    def UploadService(self) -> "UploadService":
        """Get UploadService instance.

        Returns:
            UploadService: The upload service instance using Store's session.
        """
        if self._upload_service is None:
            from services.upload_service import UploadService

            self._upload_service = UploadService(self)
        return self._upload_service

    @property
    def ImportService(self) -> "ImportService":
        """Get ImportService instance.

        Returns:
            ImportService: The import service instance using Store's session.
        """
        if self._import_service is None:
            from services.import_service import ImportService

            self._import_service = ImportService(self)
        return self._import_service

    @property
    def ExportService(self) -> "ExportService":
        """Get ExportService instance.

        Returns:
            ExportService: The export service instance using Store's session.
        """
        if self._export_service is None:
            from services.export_service import ExportService

            self._export_service = ExportService(self)
        return self._export_service

    @property
    def SettingsService(self) -> "SettingsService":
        """Get SettingsService instance.

        Returns:
            SettingsService: The settings service instance using Store's session.
        """
        if self._settings_service is None:
            from services.settings_service import SettingsService

            self._settings_service = SettingsService(self)
        return self._settings_service

    @property
    def CalendarService(self) -> "CalendarService":
        """Get CalendarService instance.

        Returns:
            CalendarService: The calendar service instance using Store's session.
        """
        if self._calendar_service is None:
            from services.calendar_service import CalendarService

            self._calendar_service = CalendarService(self)
        return self._calendar_service

    @property
    def ReminderService(self) -> "ReminderService":
        """Get ReminderService instance.

        Returns:
            ReminderService: The reminder service instance using Store's session.
        """
        if self._reminder_service is None:
            from services.reminder_service import ReminderService

            self._reminder_service = ReminderService(self)
        return self._reminder_service

    @property
    def EventService(self) -> "EventService":
        """Get EventService instance.

        Returns:
            EventService: The event service instance using Store's session.
        """
        if self._event_service is None:
            from services.event_service import EventService

            self._event_service = EventService(self)
        return self._event_service
