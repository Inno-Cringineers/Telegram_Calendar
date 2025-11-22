"""
Custom exceptions for repository layer.

These exceptions help identify where errors occurred and simplify logging.
"""


class RepositoryError(Exception):
    """Base exception for all repository errors."""

    pass


class NotFoundError(RepositoryError):
    """Raised when an entity is not found in the repository."""

    def __init__(self, entity_name: str, identifier: str | int) -> None:
        """Initialize NotFoundError.

        Args:
            entity_name: Name of the entity (e.g., "Event", "Calendar").
            identifier: The identifier that was not found (ID, etc.).
        """
        self.entity_name = entity_name
        self.identifier = identifier
        super().__init__(f"{entity_name} with identifier '{identifier}' not found")


class CalendarNotFoundError(NotFoundError):
    """Raised when a Calendar is not found."""

    def __init__(self, calendar_id: int | None = None, user_id: int | None = None) -> None:
        """Initialize CalendarNotFoundError.

        Args:
            calendar_id: The calendar ID that was not found (if applicable).
            user_id: The user ID that was used in search (if applicable).
        """
        self.calendar_id = calendar_id
        self.user_id = user_id
        identifier = f"id={calendar_id}" if calendar_id else f"user_id={user_id}"
        super().__init__("Calendar", identifier)


class EventNotFoundError(NotFoundError):
    """Raised when an Event is not found."""

    def __init__(self, event_id: int | None = None, user_id: int | None = None) -> None:
        """Initialize EventNotFoundError.

        Args:
            event_id: The event ID that was not found (if applicable).
            user_id: The user ID that was used in search (if applicable).
        """
        self.event_id = event_id
        self.user_id = user_id
        identifier = f"id={event_id}" if event_id else f"user_id={user_id}"
        super().__init__("Event", identifier)


class ValidationError(RepositoryError):
    """Raised when validation fails in repository operations."""

    def __init__(self, message: str) -> None:
        """Initialize ValidationError.

        Args:
            message: Error message describing the validation failure.
        """
        self.message = message
        super().__init__(f"Validation error: {message}")


class EventValidationError(ValidationError):
    """Raised when Event validation fails."""

    def __init__(self, message: str) -> None:
        """Initialize EventValidationError.

        Args:
            message: Error message describing the validation failure.
        """
        self.message = message
        super().__init__(f"Event validation error: {message}")


class SettingsValidationError(ValidationError):
    """Raised when Settings validation fails."""

    def __init__(self, message: str) -> None:
        """Initialize SettingsValidationError.

        Args:
            message: Error message describing the validation failure.
        """
        self.message = message
        super().__init__(f"Settings validation error: {message}")


class SettingsNotFoundError(NotFoundError):
    """Raised when Settings is not found."""

    def __init__(self, settings_id: int | None = None, user_id: int | None = None) -> None:
        """Initialize SettingsNotFoundError.

        Args:
            settings_id: The settings ID that was not found (if applicable).
            user_id: The user ID that was used in search (if applicable).
        """
        self.settings_id = settings_id
        self.user_id = user_id
        identifier = f"id={settings_id}" if settings_id else f"user_id={user_id}"
        super().__init__("Settings", identifier)
