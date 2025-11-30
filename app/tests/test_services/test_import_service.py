import tempfile
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import icalendar
import pytest

from models.event import Event
from models.reminder import Reminder
from services.import_service import ImportService


@pytest.mark.asyncio
async def test_import_external_calendar_from_real_ics_file():
    # --- create temporary ICS file ---
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

    # --- mock repositories ---
    mock_store = MagicMock()
    mock_calendar_repo = MagicMock()
    mock_event_repo = MagicMock()

    mock_store.get_calendar_repository = mock_calendar_repo
    mock_store.get_event_repository = mock_event_repo

    # calendar does not exist
    mock_calendar_repo.find = AsyncMock(return_value=[])
    mock_calendar_repo.create = AsyncMock(return_value=[MagicMock(id=1, user_id=42)])
    mock_event_repo.create = AsyncMock(return_value=[MagicMock(id=10)])

    service = ImportService(store=mock_store)

    # --- act ---
    await service.import_external_calendar_from_file(
        file_path=tmp_path,
        user_id=42,
        calendar_name="Test ICS",
        calendar_url="http://example.com",
    )

    # --- assert ---
    mock_calendar_repo.create.assert_awaited_once()
    mock_event_repo.create.assert_awaited_once()

    created_event = mock_event_repo.create.call_args[0][0][0]
    assert created_event.title == "Test Event"
    assert created_event.uid == "uid1"


@pytest.mark.asyncio
async def test_import_external_calendar_creates_new_calendar():
    mock_store = MagicMock()
    mock_calendar_repo = MagicMock()
    mock_event_repo = MagicMock()

    mock_store.get_calendar_repository = mock_calendar_repo
    mock_store.get_event_repository = mock_event_repo

    mock_calendar_repo.find = AsyncMock(return_value=[])
    mock_calendar_repo.create = AsyncMock(return_value=[MagicMock(id=1, user_id=42)])

    event = Event(
        uid="uid1",
        title="Event 1",
        description="desc",
        date_start=datetime(2025, 1, 1, 12, 0, tzinfo=UTC),
        date_end=datetime(2025, 1, 1, 13, 0, tzinfo=UTC),
    )

    with patch("services.import_service.ICSParser") as MockParser:
        MockParser.return_value.get_entities.return_value = [(event, [])]
        mock_event_repo.create = AsyncMock(return_value=[MagicMock(id=10)])

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
async def test_import_external_calendar_updates_existing_calendar():
    mock_store = MagicMock()
    mock_calendar_repo = MagicMock()
    mock_event_repo = MagicMock()

    mock_store.get_calendar_repository = mock_calendar_repo
    mock_store.get_event_repository = mock_event_repo

    existing_calendar = MagicMock(id=1, user_id=42)
    existing_calendar.url = "http://example.com"
    existing_calendar.name = "Calendar"

    event = Event(
        uid="uid1",
        title="Event 1",
        description="desc",
        date_start=datetime(2025, 1, 1, 12, 0, tzinfo=UTC),
        date_end=datetime(2025, 1, 1, 13, 0, tzinfo=UTC),
    )

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

        # existing events deleted
        mock_event_repo.delete.assert_awaited()

        # new events created
        mock_event_repo.create.assert_awaited()


@pytest.mark.asyncio
async def test_import_local_calendar_creates_new_calendar():
    mock_store = AsyncMock()
    mock_calendar_repo = AsyncMock()
    mock_event_repo = AsyncMock()
    mock_reminder_repo = AsyncMock()

    mock_store.get_calendar_repository = mock_calendar_repo
    mock_store.get_event_repository = mock_event_repo
    mock_store.get_reminder_repository = mock_reminder_repo

    mock_calendar_repo.find = AsyncMock(return_value=[])

    # no calendar exists
    mock_calendar_repo.create = AsyncMock(return_value=[MagicMock(id=1, user_id=42)])

    # event created
    mock_event_repo.create = AsyncMock(return_value=[MagicMock(id=100)])

    # reminder created
    mock_reminder_repo.create = AsyncMock()

    # Entities returned by ICSParser
    event = Event(
        uid="1",
        title="Local Event",
        description=None,
        date_start=datetime(2025, 1, 1, 12, 0, tzinfo=UTC),
        date_end=datetime(2025, 1, 1, 13, 0, tzinfo=UTC),
    )

    reminder = Reminder(
        description="Test reminder",
        trigger_offset="-PT30M",
        trigger_datetime=None,
        repeat_count=None,
        repeat_interval=None,
    )

    with patch("services.import_service.ICSParser") as MP:
        MP.return_value.get_entities.return_value = [(event, [reminder])]

        service = ImportService(store=mock_store)

        await service.import_local_calendar_from_file("dummy.ics", user_id=42)

        mock_calendar_repo.create.assert_awaited_once()
        mock_event_repo.create.assert_awaited_once()
        mock_reminder_repo.create.assert_awaited_once()

        created_event = mock_event_repo.create.call_args[0][0][0]
        assert created_event.title == "Local Event"
        assert created_event.uid == "1"


@pytest.mark.asyncio
async def test_import_local_calendar_updates_existing_event():
    mock_store = AsyncMock()
    mock_calendar_repo = AsyncMock()
    mock_event_repo = AsyncMock()
    mock_reminder_repo = AsyncMock()

    mock_store.get_calendar_repository = mock_calendar_repo
    mock_store.get_event_repository = mock_event_repo
    mock_store.get_reminder_repository = mock_reminder_repo

    calendar = MagicMock(id=1, user_id=42)

    mock_calendar_repo.create = AsyncMock(return_value=[calendar])

    existing_event = MagicMock(id=10)
    mock_event_repo.find = AsyncMock(return_value=[existing_event])

    mock_event_repo.update = AsyncMock(return_value=existing_event)
    mock_reminder_repo.find = AsyncMock(return_value=[MagicMock(id=1), MagicMock(id=2)])
    mock_reminder_repo.delete = AsyncMock()
    mock_reminder_repo.create = AsyncMock()

    event = Event(
        uid="x1",
        title="Updated Title",
        description="New Desc",
        date_start=datetime(2025, 5, 5, 10, 0, tzinfo=UTC),
        date_end=datetime(2025, 5, 5, 12, 0, tzinfo=UTC),
    )
    reminder = Reminder(description="R", trigger_offset="-PT15M")

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
async def test_import_local_calendar_generates_uid_if_missing(monkeypatch):
    mock_store = AsyncMock()
    mock_calendar_repo = AsyncMock()
    mock_event_repo = AsyncMock()
    mock_reminder_repo = AsyncMock()

    mock_store.get_calendar_repository = mock_calendar_repo
    mock_store.get_event_repository = mock_event_repo
    mock_store.get_reminder_repository = mock_reminder_repo

    mock_calendar_repo.create = AsyncMock(return_value=[MagicMock(id=1)])
    mock_event_repo.create = AsyncMock(return_value=[MagicMock(id=10)])
    mock_reminder_repo.create = AsyncMock()

    mock_event_repo.find = AsyncMock(return_value=[])

    monkeypatch.setattr("uuid.uuid4", lambda: "GENERATED-UID")

    event = Event(
        uid=None,
        title="E",
        description=None,
        date_start=datetime(2025, 2, 1, 10, 0, tzinfo=UTC),
        date_end=datetime(2025, 2, 1, 11, 0, tzinfo=UTC),
    )
    reminder = Reminder(description="R")

    with patch("services.import_service.ICSParser") as MP:
        MP.return_value.get_entities.return_value = [(event, [reminder])]

        service = ImportService(store=mock_store)

        await service.import_local_calendar_from_file("dummy.ics", user_id=1)

        created_event = mock_event_repo.create.call_args[0][0][0]
        assert created_event.uid == "GENERATED-UID"


@pytest.mark.asyncio
async def test_import_local_calendar_replaces_reminders():
    mock_store = AsyncMock()
    mock_calendar_repo = AsyncMock()
    mock_event_repo = AsyncMock()
    mock_reminder_repo = AsyncMock()

    mock_store.get_calendar_repository = mock_calendar_repo
    mock_store.get_event_repository = mock_event_repo
    mock_store.get_reminder_repository = mock_reminder_repo

    calendar = MagicMock(id=1, user_id=42)
    mock_calendar_repo.create = AsyncMock(return_value=[calendar])

    existing_event = MagicMock(id=10)
    mock_event_repo.find = AsyncMock(return_value=[existing_event])
    mock_event_repo.update = AsyncMock(return_value=existing_event)

    # existing reminders (before update)
    mock_reminder_repo.find = AsyncMock(
        return_value=[
            MagicMock(id=1),
            MagicMock(id=2),
        ]
    )
    mock_reminder_repo.delete = AsyncMock()
    mock_reminder_repo.create = AsyncMock()

    event = Event(
        uid="1",
        title="A",
        description=None,
        date_start=datetime(2025, 3, 1, 12, 0, tzinfo=UTC),
        date_end=datetime(2025, 3, 1, 13, 0, tzinfo=UTC),
    )
    reminder_new = Reminder(description="NEW", trigger_offset="-PT10M")

    with patch("services.import_service.ICSParser") as MP:
        MP.return_value.get_entities.return_value = [(event, [reminder_new])]

        service = ImportService(store=mock_store)
        await service.import_local_calendar_from_file("dummy", user_id=42)

        # old removed
        assert mock_reminder_repo.delete.await_count == 2

        # new created
        mock_reminder_repo.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_generate_uid_uniqueness(monkeypatch):
    mock_store = AsyncMock()
    mock_event_repo = AsyncMock()
    mock_store.get_event_repository = mock_event_repo

    service = ImportService(store=mock_store)

    existing_uids = {"1", "2"}

    async def mock_find(filter):
        return [{}] if filter.uid in existing_uids else []

    mock_event_repo.find = mock_find

    uids = ["1", "2", "3"]
    iter_uids = iter(uids)
    monkeypatch.setattr(uuid, "uuid4", lambda: next(iter_uids))

    uid = await service._generate_uid()
    assert uid == "3"
