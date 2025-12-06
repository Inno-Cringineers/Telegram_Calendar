"""Tests for ImportService using mocks and fixtures."""

import tempfile
import uuid
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock, patch

import icalendar
import pytest

from models.event import Event
from models.reminder import Reminder
from services.ics_parcer import VAlarmSchema, VEventSchema
from services.import_service import ImportService

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch


# ----------------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------------


@pytest.fixture
def mock_calendar_repo() -> AsyncMock:
    """Create a mock calendar repository."""
    return AsyncMock()


@pytest.fixture
def mock_event_repo() -> AsyncMock:
    """Create a mock event repository."""
    return AsyncMock()


@pytest.fixture
def mock_reminder_repo() -> AsyncMock:
    """Create a mock reminder repository."""
    return AsyncMock()


@pytest.fixture
def mock_settings_repo() -> AsyncMock:
    """Create a mock settings repository."""
    return AsyncMock()


@pytest.fixture
def mock_store(
    mock_calendar_repo: AsyncMock,
    mock_event_repo: AsyncMock,
    mock_reminder_repo: AsyncMock,
    mock_settings_repo: AsyncMock,
) -> AsyncMock:
    """Create a mock store with all repositories and services configured.

    Args:
        mock_calendar_repo: Mock calendar repository.
        mock_event_repo: Mock event repository.
        mock_reminder_repo: Mock reminder repository.
        mock_settings_repo: Mock settings repository.

    Returns:
        Mock store instance with all repositories and services configured.
    """
    store = AsyncMock()
    store.CalendarRepository = mock_calendar_repo
    store.EventRepository = mock_event_repo
    store.ReminderRepository = mock_reminder_repo
    store.SettingsRepository = mock_settings_repo

    # Mock services (ImportService uses services, not repositories directly)
    store.CalendarService = AsyncMock()
    store.EventService = AsyncMock()
    store.ReminderService = AsyncMock()
    store.SettingsService = AsyncMock()

    return store


@pytest.fixture
def sample_event() -> Event:
    """Create a sample event for testing.

    Returns:
        Event instance with default test values.
    """
    return Event(
        uid="test-uid-1",
        title="Test Event",
        description="Test description",
        date_start=datetime(2025, 1, 1, 12, 0, tzinfo=UTC),
        date_end=datetime(2025, 1, 1, 13, 0, tzinfo=UTC),
    )


@pytest.fixture
def sample_reminder() -> Reminder:
    """Create a sample reminder for testing.

    Returns:
        Reminder instance with default test values.
    """
    return Reminder(
        description="Test reminder",
        trigger_offset="-PT30M",
    )


@pytest.fixture
def import_service(mock_store: AsyncMock) -> ImportService:
    """Create an ImportService instance with mocked store.

    Args:
        mock_store: Mock store instance.

    Returns:
        ImportService instance.
    """
    return ImportService(store=mock_store)


# ----------------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------------


def create_event(
    uid: str | None = "test-uid",
    title: str = "Test Event",
    description: str | None = None,
    date_start: datetime | None = None,
    date_end: datetime | None = None,
) -> Event:
    """Create an Event instance with custom values.

    Args:
        uid: Event UID. Defaults to "test-uid".
        title: Event title. Defaults to "Test Event".
        description: Event description. Defaults to None.
        date_start: Event start datetime. Defaults to 2025-01-01 12:00 UTC.
        date_end: Event end datetime. Defaults to 2025-01-01 13:00 UTC.

    Returns:
        Event instance.
    """
    if date_start is None:
        date_start = datetime(2025, 1, 1, 12, 0, tzinfo=UTC)
    if date_end is None:
        date_end = datetime(2025, 1, 1, 13, 0, tzinfo=UTC)

    return Event(
        uid=uid,
        title=title,
        description=description,
        date_start=date_start,
        date_end=date_end,
    )


def create_reminder(
    description: str = "Test reminder",
    trigger_offset: str | None = "-PT30M",
) -> Reminder:
    """Create a Reminder instance with custom values.

    Args:
        description: Reminder description. Defaults to "Test reminder".
        trigger_offset: Trigger offset in RFC 5545 format. Defaults to "-PT30M".

    Returns:
        Reminder instance.
    """
    return Reminder(
        description=description,
        trigger_offset=trigger_offset,
    )


# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_import_external_calendar_from_real_ics_file(
    mock_store: AsyncMock, mock_calendar_repo: AsyncMock, mock_event_repo: AsyncMock
) -> None:
    """Test importing external calendar from a real ICS file.

    Args:
        mock_store: Mock store instance.
        mock_calendar_repo: Mock calendar repository.
        mock_event_repo: Mock event repository.
    """
    # Create temporary ICS file
    cal = icalendar.Calendar()
    cal.add("PRODID", "-//Test Calendar//")
    cal.add("VERSION", "2.0")

    event = icalendar.Event()
    event.add("UID", "uid1")
    event.add("SUMMARY", "Test Event")
    start = datetime(2025, 12, 1, 12, 0, tzinfo=UTC)
    end = start + timedelta(hours=1)
    event.add("DTSTART", start)
    event.add("DTEND", end)
    cal.add_component(event)

    with tempfile.NamedTemporaryFile("wb", delete=False, suffix=".ics") as f:
        f.write(cal.to_ical())
        tmp_path = f.name

    # Configure mocks
    mock_store.CalendarService.find = AsyncMock(return_value=[])
    created_calendar = MagicMock(id=1, user_id=42)
    mock_store.CalendarService.create = AsyncMock(return_value=created_calendar)
    mock_store.EventService.find = AsyncMock(return_value=[])  # Event doesn't exist yet
    created_event = MagicMock(id=10, title="Test Event", uid="uid1")
    mock_store.EventService.create = AsyncMock(return_value=created_event)

    service = ImportService(store=mock_store)

    # Act
    await service.import_external_calendar_from_file(
        file_path=tmp_path,
        user_id=42,
        calendar_name="Test ICS",
        calendar_url="http://example.com",
    )

    # Assert
    mock_store.CalendarService.create.assert_awaited_once()
    mock_store.EventService.create.assert_awaited_once()

    created_event_call = mock_store.EventService.create.call_args[0][0]
    assert created_event_call.title == "Test Event"
    assert created_event_call.uid == "uid1"


@pytest.mark.asyncio
async def test_import_external_calendar_creates_new_calendar(
    mock_store: AsyncMock, mock_calendar_repo: AsyncMock, mock_event_repo: AsyncMock, sample_event: Event
) -> None:
    """Test creating a new external calendar when it doesn't exist.

    Args:
        mock_store: Mock store instance.
        mock_calendar_repo: Mock calendar repository.
        mock_event_repo: Mock event repository.
        sample_event: Sample event fixture.
    """
    mock_store.CalendarService.find = AsyncMock(return_value=[])
    created_calendar = MagicMock(id=1, user_id=42)
    mock_store.CalendarService.create = AsyncMock(return_value=created_calendar)
    mock_store.EventService.find = AsyncMock(return_value=[])  # Event doesn't exist yet
    created_event = MagicMock(id=10)
    mock_store.EventService.create = AsyncMock(return_value=created_event)

    event_schema = VEventSchema(
        uid="uid1",
        title="Event 1",
        description="desc",
        date_start=datetime(2025, 1, 1, 12, 0, tzinfo=UTC),
        date_end=datetime(2025, 1, 1, 13, 0, tzinfo=UTC),
        rrule=None,
        rdate=None,
        exdate=None,
        alarms=None,
    )

    with patch("services.import_service.ICSParser") as MockParser:
        MockParser.return_value.get_schemas.return_value = [event_schema]

        service = ImportService(store=mock_store)

        await service.import_external_calendar_from_file(
            "fake.ics",
            user_id=42,
            calendar_name="Calendar",
            calendar_url="http://example.com",
        )

        mock_store.CalendarService.create.assert_awaited_once()
        mock_store.EventService.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_import_external_calendar_updates_existing_calendar(
    mock_store: AsyncMock, mock_calendar_repo: AsyncMock, mock_event_repo: AsyncMock
) -> None:
    """Test updating an existing external calendar.

    Args:
        mock_store: Mock store instance.
        mock_calendar_repo: Mock calendar repository.
        mock_event_repo: Mock event repository.
    """
    existing_calendar = MagicMock(id=1, user_id=42)
    existing_calendar.url = "http://example.com"
    existing_calendar.name = "Calendar"

    event_schema = VEventSchema(
        uid="uid1",
        title="Event 1",
        description="desc",
        date_start=datetime(2025, 1, 1, 12, 0, tzinfo=UTC),
        date_end=datetime(2025, 1, 1, 13, 0, tzinfo=UTC),
        rrule=None,
        rdate=None,
        exdate=None,
        alarms=None,
    )

    with patch("services.import_service.ICSParser") as MockParser:
        MockParser.return_value.get_schemas.return_value = [event_schema]

        mock_store.CalendarService.find = AsyncMock(return_value=[existing_calendar])
        existing_event = MagicMock(id=10)
        mock_store.EventService.find = AsyncMock(return_value=[existing_event])
        mock_store.EventService.update_by_id = AsyncMock(return_value=existing_event)
        created_event = MagicMock(id=20)
        mock_store.EventService.create = AsyncMock(return_value=created_event)

        service = ImportService(store=mock_store)

        await service.import_external_calendar_from_file(
            "fake.ics",
            user_id=42,
            calendar_name="Calendar",
            calendar_url="http://example.com",
        )

        # For external calendars, alarms are set to None, so no reminders are created
        # Event exists, so it should be updated, not created
        mock_store.EventService.update_by_id.assert_awaited_once()
        mock_store.EventService.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_import_local_calendar_creates_new_calendar(
    mock_store: AsyncMock,
    mock_calendar_repo: AsyncMock,
    mock_event_repo: AsyncMock,
    mock_reminder_repo: AsyncMock,
    mock_settings_repo: AsyncMock,
) -> None:
    """Test creating a new local calendar when it doesn't exist.

    Args:
        mock_store: Mock store instance.
        mock_calendar_repo: Mock calendar repository.
        mock_event_repo: Mock event repository.
        mock_reminder_repo: Mock reminder repository.
        mock_settings_repo: Mock settings repository.
    """
    mock_store.CalendarService.get_by_user_id = AsyncMock(return_value=[])
    created_calendar = MagicMock(id=1, user_id=42)
    mock_store.CalendarService.create = AsyncMock(return_value=created_calendar)
    mock_store.EventService.find = AsyncMock(return_value=[])  # Event doesn't exist yet
    created_event = MagicMock(id=100, title="Local Event", uid="1")
    mock_store.EventService.create = AsyncMock(return_value=created_event)
    mock_store.ReminderService.create = AsyncMock()
    mock_settings = MagicMock(id=1, user_id=42, default_reminder_offset=15 * 60)
    mock_store.SettingsService.get_by_id = AsyncMock(return_value=mock_settings)

    alarm = VAlarmSchema(description="Test reminder", trigger_offset="-PT30M", trigger_datetime=None)
    event_schema = VEventSchema(
        uid="1",
        title="Local Event",
        description=None,
        date_start=datetime(2025, 1, 1, 12, 0, tzinfo=UTC),
        date_end=datetime(2025, 1, 1, 13, 0, tzinfo=UTC),
        rrule=None,
        rdate=None,
        exdate=None,
        alarms=[alarm],
    )

    with patch("services.import_service.ICSParser") as MP:
        MP.return_value.get_schemas.return_value = [event_schema]

        service = ImportService(store=mock_store)

        await service.import_local_calendar_from_file("dummy.ics", user_id=42)

        mock_store.CalendarService.create.assert_awaited_once()
        mock_store.EventService.create.assert_awaited_once()
        mock_store.ReminderService.create.assert_awaited()

        created_event_call = mock_store.EventService.create.call_args[0][0]
        assert created_event_call.title == "Local Event"
        assert created_event_call.uid == "1"


@pytest.mark.asyncio
async def test_import_local_calendar_updates_existing_event(
    mock_store: AsyncMock,
    mock_calendar_repo: AsyncMock,
    mock_event_repo: AsyncMock,
    mock_reminder_repo: AsyncMock,
    mock_settings_repo: AsyncMock,
) -> None:
    """Test updating an existing event in local calendar.

    Args:
        mock_store: Mock store instance.
        mock_calendar_repo: Mock calendar repository.
        mock_event_repo: Mock event repository.
        mock_reminder_repo: Mock reminder repository.
        mock_settings_repo: Mock settings repository.
    """
    calendar = MagicMock(id=1, user_id=42)
    mock_store.CalendarService.get_by_user_id = AsyncMock(return_value=[calendar])

    existing_event = MagicMock(id=10)
    mock_store.EventService.find = AsyncMock(return_value=[existing_event])
    mock_store.EventService.update_by_id = AsyncMock(return_value=existing_event)
    mock_store.ReminderService.delete_by_event_id = AsyncMock()
    mock_store.ReminderService.create = AsyncMock()
    mock_store.SettingsService.get_by_id = AsyncMock(return_value=None)  # No settings, so no default reminder

    alarm = VAlarmSchema(description="R", trigger_offset="-PT15M", trigger_datetime=None)
    event_schema = VEventSchema(
        uid="x1",
        title="Updated Title",
        description="New Desc",
        date_start=datetime(2025, 5, 5, 10, 0, tzinfo=UTC),
        date_end=datetime(2025, 5, 5, 12, 0, tzinfo=UTC),
        rrule=None,
        rdate=None,
        exdate=None,
        alarms=[alarm],
    )

    with patch("services.import_service.ICSParser") as MP:
        MP.return_value.get_schemas.return_value = [event_schema]

        service = ImportService(store=mock_store)

        await service.import_local_calendar_from_file("dummy.ics", user_id=42)

        mock_store.EventService.update_by_id.assert_awaited_once()

        updated_call = mock_store.EventService.update_by_id.call_args[0]
        assert updated_call[0] == 10  # event.id
        update_schema = updated_call[1]
        assert update_schema.title == "Updated Title"


@pytest.mark.asyncio
async def test_import_local_calendar_generates_uid_if_missing(
    mock_store: AsyncMock,
    mock_calendar_repo: AsyncMock,
    mock_event_repo: AsyncMock,
    mock_reminder_repo: AsyncMock,
    mock_settings_repo: AsyncMock,
    monkeypatch: "MonkeyPatch",
) -> None:
    """Test that UID is generated when event doesn't have one.

    Args:
        mock_store: Mock store instance.
        mock_calendar_repo: Mock calendar repository.
        mock_event_repo: Mock event repository.
        mock_reminder_repo: Mock reminder repository.
        mock_settings_repo: Mock settings repository.
        monkeypatch: Pytest monkeypatch fixture.
    """
    mock_store.CalendarService.get_by_user_id = AsyncMock(return_value=[])
    created_calendar = MagicMock(id=1)
    mock_store.CalendarService.create = AsyncMock(return_value=created_calendar)
    created_event_mock = MagicMock(id=10, date_start=datetime(2025, 2, 1, 10, 0, tzinfo=UTC), uid="GENERATED-UID")
    mock_store.EventService.create = AsyncMock(return_value=created_event_mock)
    mock_store.EventService.find = AsyncMock(return_value=[])
    mock_store.ReminderService.create = AsyncMock()
    # No settings, so no default reminder
    mock_store.SettingsService.get_by_id = AsyncMock(return_value=None)

    def mock_uuid4() -> str:
        """Mock uuid4 that returns a fixed value."""
        return "GENERATED-UID"

    monkeypatch.setattr("uuid.uuid4", mock_uuid4)

    alarm = VAlarmSchema(description="R", trigger_offset=None, trigger_datetime=None)
    event_schema = VEventSchema(
        uid=None,
        title="E",
        description=None,
        date_start=datetime(2025, 2, 1, 10, 0, tzinfo=UTC),
        date_end=datetime(2025, 2, 1, 11, 0, tzinfo=UTC),
        rrule=None,
        rdate=None,
        exdate=None,
        alarms=[alarm],
    )

    with patch("services.import_service.ICSParser") as MP:
        MP.return_value.get_schemas.return_value = [event_schema]

        service = ImportService(store=mock_store)

        await service.import_local_calendar_from_file("dummy.ics", user_id=1)

        created_event_call = mock_store.EventService.create.call_args[0][0]
        assert created_event_call.uid == "GENERATED-UID"


@pytest.mark.asyncio
async def test_import_local_calendar_replaces_reminders(
    mock_store: AsyncMock,
    mock_calendar_repo: AsyncMock,
    mock_event_repo: AsyncMock,
    mock_reminder_repo: AsyncMock,
    mock_settings_repo: AsyncMock,
) -> None:
    """Test that old reminders are replaced when updating an event.

    Args:
        mock_store: Mock store instance.
        mock_calendar_repo: Mock calendar repository.
        mock_event_repo: Mock event repository.
        mock_reminder_repo: Mock reminder repository.
        mock_settings_repo: Mock settings repository.
    """
    calendar = MagicMock(id=1, user_id=42)
    mock_store.CalendarService.get_by_user_id = AsyncMock(return_value=[calendar])

    existing_event = MagicMock(id=10)
    mock_store.EventService.find = AsyncMock(return_value=[existing_event])
    mock_store.EventService.update_by_id = AsyncMock(return_value=existing_event)

    # Existing reminders (before update)
    mock_store.ReminderService.delete_by_event_id = AsyncMock()
    mock_store.ReminderService.create = AsyncMock()
    mock_store.SettingsService.get_by_id = AsyncMock(return_value=None)  # No settings, so no default reminder

    alarm_new = VAlarmSchema(description="NEW", trigger_offset="-PT10M", trigger_datetime=None)
    event_schema = VEventSchema(
        uid="1",
        title="A",
        description=None,
        date_start=datetime(2025, 3, 1, 12, 0, tzinfo=UTC),
        date_end=datetime(2025, 3, 1, 13, 0, tzinfo=UTC),
        rrule=None,
        rdate=None,
        exdate=None,
        alarms=[alarm_new],
    )

    with patch("services.import_service.ICSParser") as MP:
        MP.return_value.get_schemas.return_value = [event_schema]

        service = ImportService(store=mock_store)
        await service.import_local_calendar_from_file("dummy", user_id=42)

        # Old reminders removed (delete_by_event_id is called once for the event)
        mock_store.ReminderService.delete_by_event_id.assert_awaited_once()

        # New reminders created
        mock_store.ReminderService.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_generate_uid_uniqueness(
    mock_store: AsyncMock, mock_event_repo: AsyncMock, monkeypatch: "MonkeyPatch"
) -> None:
    """Test that UID generation ensures uniqueness by checking existing UIDs.

    Args:
        mock_store: Mock store instance.
        mock_event_repo: Mock event repository.
        monkeypatch: Pytest monkeypatch fixture.
    """
    service = ImportService(store=mock_store)

    existing_uids = {"1", "2"}

    async def mock_find(filter: Any) -> list[dict]:
        """Mock find method that returns non-empty list if UID exists."""
        return [{}] if filter.uid in existing_uids else []

    mock_store.EventService.find = mock_find

    uids = ["1", "2", "3"]
    iter_uids = iter(uids)

    def mock_uuid4() -> str:
        """Mock uuid4 that returns values from the iterator."""
        try:
            return next(iter_uids)
        except StopIteration:
            return "fallback-uid"

    monkeypatch.setattr(uuid, "uuid4", mock_uuid4)

    uid = await service._generate_uid()
    assert uid == "3"
