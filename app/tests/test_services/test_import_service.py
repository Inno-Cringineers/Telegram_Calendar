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
) -> MagicMock:
    """Create a mock store with all repositories configured.

    Args:
        mock_calendar_repo: Mock calendar repository.
        mock_event_repo: Mock event repository.
        mock_reminder_repo: Mock reminder repository.
        mock_settings_repo: Mock settings repository.

    Returns:
        Mock store instance with all repositories configured.
    """
    store = MagicMock()
    store.get_calendar_repository = mock_calendar_repo
    store.get_event_repository = mock_event_repo
    store.get_reminder_repository = mock_reminder_repo
    store.get_settings_repository = mock_settings_repo
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
        trigger_datetime=None,
        repeat_count=None,
        repeat_interval=None,
    )


@pytest.fixture
def import_service(mock_store: MagicMock) -> ImportService:
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
    trigger_datetime: datetime | None = None,
    repeat_count: int | None = None,
    repeat_interval: str | None = None,
) -> Reminder:
    """Create a Reminder instance with custom values.

    Args:
        description: Reminder description. Defaults to "Test reminder".
        trigger_offset: Trigger offset in RFC 5545 format. Defaults to "-PT30M".
        trigger_datetime: Trigger datetime. Defaults to None.
        repeat_count: Repeat count. Defaults to None.
        repeat_interval: Repeat interval. Defaults to None.

    Returns:
        Reminder instance.
    """
    return Reminder(
        description=description,
        trigger_offset=trigger_offset,
        trigger_datetime=trigger_datetime,
        repeat_count=repeat_count,
        repeat_interval=repeat_interval,
    )


# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_import_external_calendar_from_real_ics_file(
    mock_store: MagicMock, mock_calendar_repo: AsyncMock, mock_event_repo: AsyncMock
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
    mock_calendar_repo.find = AsyncMock(return_value=[])
    mock_calendar_repo.create = AsyncMock(return_value=[MagicMock(id=1, user_id=42)])
    mock_event_repo.create = AsyncMock(return_value=[MagicMock(id=10)])

    service = ImportService(store=mock_store)

    # Act
    await service.import_external_calendar_from_file(
        file_path=tmp_path,
        user_id=42,
        calendar_name="Test ICS",
        calendar_url="http://example.com",
    )

    # Assert
    mock_calendar_repo.create.assert_awaited_once()
    mock_event_repo.create.assert_awaited_once()

    created_event = mock_event_repo.create.call_args[0][0][0]
    assert created_event.title == "Test Event"
    assert created_event.uid == "uid1"


@pytest.mark.asyncio
async def test_import_external_calendar_creates_new_calendar(
    mock_store: MagicMock, mock_calendar_repo: AsyncMock, mock_event_repo: AsyncMock, sample_event: Event
) -> None:
    """Test creating a new external calendar when it doesn't exist.

    Args:
        mock_store: Mock store instance.
        mock_calendar_repo: Mock calendar repository.
        mock_event_repo: Mock event repository.
        sample_event: Sample event fixture.
    """
    mock_calendar_repo.find = AsyncMock(return_value=[])
    mock_calendar_repo.create = AsyncMock(return_value=[MagicMock(id=1, user_id=42)])
    mock_event_repo.create = AsyncMock(return_value=[MagicMock(id=10)])

    event = create_event(uid="uid1", title="Event 1", description="desc")

    with patch("services.import_service.ICSParser") as MockParser:
        MockParser.return_value.get_entities.return_value = [(event, [])]

        service = ImportService(store=mock_store)

        await service.import_external_calendar_from_file(
            "fake.ics",
            user_id=42,
            calendar_name="Calendar",
            calendar_url="http://example.com",
        )

        mock_calendar_repo.create.assert_awaited_once()
        mock_event_repo.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_import_external_calendar_updates_existing_calendar(
    mock_store: MagicMock, mock_calendar_repo: AsyncMock, mock_event_repo: AsyncMock
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

    event = create_event(uid="uid1", title="Event 1", description="desc")

    with patch("services.import_service.ICSParser") as MockParser:
        MockParser.return_value.get_entities.return_value = [(event, [])]

        mock_calendar_repo.find = AsyncMock(return_value=[existing_calendar])
        mock_event_repo.find = AsyncMock(return_value=[MagicMock(id=10)])
        mock_event_repo.delete = AsyncMock()
        mock_event_repo.create = AsyncMock(return_value=[MagicMock(id=20)])

        service = ImportService(store=mock_store)

        await service.import_external_calendar_from_file(
            "fake.ics",
            user_id=42,
            calendar_name="Calendar",
            calendar_url="http://example.com",
        )

        # Existing events deleted
        mock_event_repo.delete.assert_awaited()

        # New events created
        mock_event_repo.create.assert_awaited()


@pytest.mark.asyncio
async def test_import_local_calendar_creates_new_calendar(
    mock_store: MagicMock,
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
    mock_calendar_repo.find = AsyncMock(return_value=[])
    mock_calendar_repo.create = AsyncMock(return_value=[MagicMock(id=1, user_id=42)])
    mock_event_repo.create = AsyncMock(return_value=[MagicMock(id=100)])
    mock_reminder_repo.create = AsyncMock()
    mock_settings_repo.get_by_id = AsyncMock(return_value=MagicMock(id=1, user_id=42, default_reminder_offset=15 * 60))

    event = create_event(uid="1", title="Local Event", description=None)
    reminder = create_reminder(description="Test reminder", trigger_offset="-PT30M")

    with patch("services.import_service.ICSParser") as MP:
        MP.return_value.get_entities.return_value = [(event, [reminder])]

        service = ImportService(store=mock_store)

        await service.import_local_calendar_from_file("dummy.ics", user_id=42)

        mock_calendar_repo.create.assert_awaited_once()
        mock_event_repo.create.assert_awaited_once()
        mock_reminder_repo.create.assert_awaited()
        mock_settings_repo.get_by_id.assert_awaited_once()

        created_event = mock_event_repo.create.call_args[0][0][0]
        assert created_event.title == "Local Event"
        assert created_event.uid == "1"


@pytest.mark.asyncio
async def test_import_local_calendar_updates_existing_event(
    mock_store: MagicMock,
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
    mock_calendar_repo.find = AsyncMock(return_value=[calendar])

    existing_event = MagicMock(id=10)
    mock_event_repo.find = AsyncMock(return_value=[existing_event])
    mock_event_repo.update = AsyncMock(return_value=existing_event)
    mock_reminder_repo.find = AsyncMock(return_value=[MagicMock(id=1), MagicMock(id=2)])
    mock_reminder_repo.delete = AsyncMock()
    mock_reminder_repo.create = AsyncMock()
    mock_settings_repo.get_by_id = AsyncMock(return_value=None)  # No settings, so no default reminder

    event = create_event(
        uid="x1",
        title="Updated Title",
        description="New Desc",
        date_start=datetime(2025, 5, 5, 10, 0, tzinfo=UTC),
        date_end=datetime(2025, 5, 5, 12, 0, tzinfo=UTC),
    )
    reminder = create_reminder(description="R", trigger_offset="-PT15M")

    with patch("services.import_service.ICSParser") as MP:
        MP.return_value.get_entities.return_value = [(event, [reminder])]

        service = ImportService(store=mock_store)

        await service.import_local_calendar_from_file("dummy.ics", user_id=42)

        mock_event_repo.update.assert_awaited_once()

        updated_call = mock_event_repo.update.call_args[0]
        assert updated_call[0] == 10  # event.id
        update_schema = updated_call[1]
        assert update_schema.title == "Updated Title"


@pytest.mark.asyncio
async def test_import_local_calendar_generates_uid_if_missing(
    mock_store: MagicMock,
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
    mock_calendar_repo.find = AsyncMock(return_value=[])
    mock_calendar_repo.create = AsyncMock(return_value=[MagicMock(id=1)])
    created_event_mock = MagicMock(id=10, date_start=datetime(2025, 2, 1, 10, 0, tzinfo=UTC))
    mock_event_repo.create = AsyncMock(return_value=[created_event_mock])
    mock_event_repo.find = AsyncMock(return_value=[])
    mock_reminder_repo.create = AsyncMock()
    # No settings, so no default reminder
    mock_settings_repo.get_by_id = AsyncMock(return_value=None)

    monkeypatch.setattr("uuid.uuid4", lambda: "GENERATED-UID")

    event = create_event(
        uid=None,
        title="E",
        description=None,
        date_start=datetime(2025, 2, 1, 10, 0, tzinfo=UTC),
        date_end=datetime(2025, 2, 1, 11, 0, tzinfo=UTC),
    )
    reminder = create_reminder(description="R")

    with patch("services.import_service.ICSParser") as MP:
        MP.return_value.get_entities.return_value = [(event, [reminder])]

        service = ImportService(store=mock_store)

        await service.import_local_calendar_from_file("dummy.ics", user_id=1)

        created_event = mock_event_repo.create.call_args[0][0][0]
        assert created_event.uid == "GENERATED-UID"


@pytest.mark.asyncio
async def test_import_local_calendar_replaces_reminders(
    mock_store: MagicMock,
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
    mock_calendar_repo.find = AsyncMock(return_value=[calendar])

    existing_event = MagicMock(id=10)
    mock_event_repo.find = AsyncMock(return_value=[existing_event])
    mock_event_repo.update = AsyncMock(return_value=existing_event)

    # Existing reminders (before update)
    mock_reminder_repo.find = AsyncMock(return_value=[MagicMock(id=1), MagicMock(id=2)])
    mock_reminder_repo.delete = AsyncMock()
    mock_reminder_repo.create = AsyncMock()
    mock_settings_repo.get_by_id = AsyncMock(return_value=None)  # No settings, so no default reminder

    event = create_event(
        uid="1",
        title="A",
        description=None,
        date_start=datetime(2025, 3, 1, 12, 0, tzinfo=UTC),
        date_end=datetime(2025, 3, 1, 13, 0, tzinfo=UTC),
    )
    reminder_new = create_reminder(description="NEW", trigger_offset="-PT10M")

    with patch("services.import_service.ICSParser") as MP:
        MP.return_value.get_entities.return_value = [(event, [reminder_new])]

        service = ImportService(store=mock_store)
        await service.import_local_calendar_from_file("dummy", user_id=42)

        # Old reminders removed
        assert mock_reminder_repo.delete.await_count == 2

        # New reminders created
        mock_reminder_repo.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_generate_uid_uniqueness(
    mock_store: MagicMock, mock_event_repo: AsyncMock, monkeypatch: "MonkeyPatch"
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

    mock_event_repo.find = mock_find

    uids = ["1", "2", "3"]
    iter_uids = iter(uids)
    monkeypatch.setattr(uuid, "uuid4", lambda: next(iter_uids))

    uid = await service._generate_uid()
    assert uid == "3"
