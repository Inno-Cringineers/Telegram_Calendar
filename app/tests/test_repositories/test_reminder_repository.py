"""Tests for ReminderRepository using mocks."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, call

import pytest

from models.reminder import Reminder
from repositories.exceptions import ReminderNotFoundError
from repositories.reminder_repository import ReminderRepository
from repositories.schemas import ReminderCreateSchema, ReminderUpdateSchema


@pytest.fixture
def mock_session() -> AsyncMock:
    """Create a mock AsyncSession."""
    session = AsyncMock()
    session.get = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.delete = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def reminder_repository(mock_session: AsyncMock) -> ReminderRepository:
    """Create a ReminderRepository instance with mocked session."""
    return ReminderRepository(mock_session)


@pytest.fixture
def sample_reminder() -> Reminder:
    """Create a sample Reminder instance for testing."""
    reminder = Reminder(
        event_id=1,
        description="Test reminder",
        trigger_offset="-PT30M",
        trigger_datetime=datetime(2025, 1, 1, 10, 0, tzinfo=UTC),
        repeat_count=3,
        repeat_interval="PT5M",
        sent=False,
    )
    # Set id manually for testing (normally set by database)
    reminder.id = 1
    return reminder


@pytest.mark.asyncio
async def test_get_by_id_returns_reminder(
    reminder_repository: ReminderRepository, mock_session: AsyncMock, sample_reminder: Reminder
) -> None:
    """Test that get_by_id returns reminder when found."""
    mock_session.get.return_value = sample_reminder

    result = await reminder_repository.get_by_id(1)

    assert result is sample_reminder
    mock_session.get.assert_called_once_with(Reminder, 1)


@pytest.mark.asyncio
async def test_get_by_id_returns_none_when_not_found(
    reminder_repository: ReminderRepository, mock_session: AsyncMock
) -> None:
    """Test that get_by_id returns None when reminder not found."""
    mock_session.get.return_value = None

    result = await reminder_repository.get_by_id(999)

    assert result is None
    mock_session.get.assert_called_once_with(Reminder, 999)


@pytest.mark.asyncio
async def test_create_creates_reminder(reminder_repository: ReminderRepository, mock_session: AsyncMock) -> None:
    """Test that create creates a new reminder."""
    trigger_dt = datetime(2025, 1, 1, 10, 0, tzinfo=UTC)
    create_data = [
        ReminderCreateSchema(  # type: ignore[call-arg]
            event_id=1,
            description="New reminder",
            trigger_offset="-PT30M",
            trigger_datetime=trigger_dt,
            repeat_count=5,
            repeat_interval="PT10M",
        )
    ]

    result = await reminder_repository.create(create_data)

    assert len(result) == 1
    assert isinstance(result[0], Reminder)
    assert result[0].event_id == 1
    assert result[0].description == "New reminder"
    assert result[0].trigger_offset == "-PT30M"
    assert result[0].trigger_datetime == trigger_dt
    assert result[0].repeat_count == 5
    assert result[0].repeat_interval == "PT10M"
    assert result[0].sent is False  # Should be set to False by default
    mock_session.add.assert_called_once_with(result[0])
    mock_session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_create_creates_multiple_reminders(
    reminder_repository: ReminderRepository, mock_session: AsyncMock
) -> None:
    """Test that create creates multiple reminders."""
    trigger_dt1 = datetime(2025, 1, 1, 10, 0, tzinfo=UTC)
    trigger_dt2 = datetime(2025, 1, 2, 10, 0, tzinfo=UTC)
    create_data = [
        ReminderCreateSchema(event_id=1, trigger_offset="-PT30M", trigger_datetime=trigger_dt1),  # type: ignore[call-arg]
        ReminderCreateSchema(event_id=2, trigger_offset="-PT1H", trigger_datetime=trigger_dt2),  # type: ignore[call-arg]
    ]

    result = await reminder_repository.create(create_data)

    assert isinstance(result, list)
    assert len(result) == 2
    assert isinstance(result[0], Reminder)
    assert result[0].event_id == 1
    assert isinstance(result[1], Reminder)
    assert result[1].event_id == 2
    mock_session.add.assert_has_calls([call(result[0]), call(result[1])], any_order=True)
    assert mock_session.flush.call_count == 2


@pytest.mark.asyncio
async def test_create_creates_reminder_with_minimal_data(
    reminder_repository: ReminderRepository, mock_session: AsyncMock
) -> None:
    """Test that create creates reminder with minimal required data."""
    trigger_dt = datetime(2025, 1, 1, 10, 0, tzinfo=UTC)
    create_data = [
        ReminderCreateSchema(event_id=1, trigger_offset="-PT30M", trigger_datetime=trigger_dt)  # type: ignore[call-arg]
    ]

    result = await reminder_repository.create(create_data)

    assert len(result) == 1
    reminder = result[0]
    assert reminder.event_id == 1
    assert reminder.trigger_offset == "-PT30M"
    assert reminder.trigger_datetime == trigger_dt
    assert reminder.description is None
    assert reminder.repeat_count is None
    assert reminder.repeat_interval is None
    assert reminder.sent is False


@pytest.mark.asyncio
async def test_update_updates_existing_reminder(
    reminder_repository: ReminderRepository, mock_session: AsyncMock, sample_reminder: Reminder
) -> None:
    """Test that update updates an existing reminder."""
    mock_session.get.return_value = sample_reminder
    update_data = ReminderUpdateSchema(description="Updated reminder")  # type: ignore[call-arg]

    result = await reminder_repository.update(1, update_data)

    assert result is sample_reminder
    assert result.description == "Updated reminder"
    mock_session.get.assert_called_once_with(Reminder, 1)
    mock_session.flush.assert_called_once()
    mock_session.refresh.assert_called_once_with(sample_reminder)


@pytest.mark.asyncio
async def test_update_updates_multiple_fields(
    reminder_repository: ReminderRepository, mock_session: AsyncMock, sample_reminder: Reminder
) -> None:
    """Test that update can update multiple fields."""
    mock_session.get.return_value = sample_reminder
    new_trigger_dt = datetime(2025, 1, 2, 10, 0, tzinfo=UTC)
    update_data = ReminderUpdateSchema(  # type: ignore[call-arg]
        description="Updated description",
        trigger_offset="-PT1H",
        trigger_datetime=new_trigger_dt,
        repeat_count=10,
        repeat_interval="PT15M",
    )

    result = await reminder_repository.update(1, update_data)

    assert result.description == "Updated description"
    assert result.trigger_offset == "-PT1H"
    assert result.trigger_datetime == new_trigger_dt
    assert result.repeat_count == 10
    assert result.repeat_interval == "PT15M"


@pytest.mark.asyncio
async def test_update_raises_error_when_reminder_not_found(
    reminder_repository: ReminderRepository, mock_session: AsyncMock
) -> None:
    """Test that update raises ReminderNotFoundError when reminder not found."""
    mock_session.get.return_value = None
    update_data = ReminderUpdateSchema(description="Updated reminder")  # type: ignore[call-arg]

    with pytest.raises(ReminderNotFoundError) as exc_info:
        await reminder_repository.update(999, update_data)

    assert exc_info.value.reminder_id == 999
    mock_session.get.assert_called_once_with(Reminder, 999)
    mock_session.flush.assert_not_called()


@pytest.mark.asyncio
async def test_update_only_updates_provided_fields(
    reminder_repository: ReminderRepository, mock_session: AsyncMock, sample_reminder: Reminder
) -> None:
    """Test that update only updates fields provided in schema."""
    original_description = sample_reminder.description
    original_trigger_offset = sample_reminder.trigger_offset
    mock_session.get.return_value = sample_reminder
    update_data = ReminderUpdateSchema(repeat_count=10)  # type: ignore[call-arg]

    result = await reminder_repository.update(1, update_data)

    assert result.description == original_description  # Not changed
    assert result.trigger_offset == original_trigger_offset  # Not changed
    assert result.repeat_count == 10  # Changed
    mock_session.flush.assert_called_once()
    mock_session.refresh.assert_called_once_with(sample_reminder)


@pytest.mark.asyncio
async def test_find_returns_reminder_by_event_id(
    reminder_repository: ReminderRepository, mock_session: AsyncMock, sample_reminder: Reminder
) -> None:
    """Test that find returns reminder when found by event_id."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [sample_reminder]
    mock_session.execute.return_value = mock_result

    result = await reminder_repository.find(1)

    assert result == [sample_reminder]
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_find_returns_none_when_not_found(
    reminder_repository: ReminderRepository, mock_session: AsyncMock
) -> None:
    """Test that find returns None when reminder not found by event_id."""
    mock_result = MagicMock()
    mock_result.scalar.return_value = None
    mock_session.execute.return_value = mock_result

    result = await reminder_repository.find(999)

    assert result == []
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_delete_deletes_reminder(
    reminder_repository: ReminderRepository, mock_session: AsyncMock, sample_reminder: Reminder
) -> None:
    """Test that delete deletes an existing reminder."""
    mock_session.get.return_value = sample_reminder

    await reminder_repository.delete(1)

    mock_session.get.assert_called_once_with(Reminder, 1)
    mock_session.delete.assert_called_once_with(sample_reminder)
    mock_session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_delete_raises_error_when_reminder_not_found(
    reminder_repository: ReminderRepository, mock_session: AsyncMock
) -> None:
    """Test that delete raises ReminderNotFoundError when reminder not found."""
    mock_session.get.return_value = None

    with pytest.raises(ReminderNotFoundError) as exc_info:
        await reminder_repository.delete(999)

    assert exc_info.value.reminder_id == 999
    mock_session.get.assert_called_once_with(Reminder, 999)
    mock_session.delete.assert_not_called()
    mock_session.flush.assert_not_called()
