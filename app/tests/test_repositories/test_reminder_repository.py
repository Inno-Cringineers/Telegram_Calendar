"""Tests for ReminderRepository using mocks."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from models.reminder import Reminder
from repositories.exceptions import ReminderNotFoundError
from repositories.reminder_repository import ReminderRepository
from repositories.schemas import ReminderCreateSchema, ReminderFilter, ReminderResponse, ReminderUpdateSchema


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

    assert result == ReminderResponse.from_model(sample_reminder)
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
    create_data = ReminderCreateSchema(
        event_id=1,
        description="New reminder",
        trigger_offset="-PT30M",
        sent=False,
    )

    await reminder_repository.create_one(create_data)

    mock_session.add.assert_called_once()
    mock_session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_create_many_creates_multiple_reminders(
    reminder_repository: ReminderRepository, mock_session: AsyncMock
) -> None:
    """Test that create_many creates multiple reminders."""
    create_data = [
        ReminderCreateSchema(event_id=1, description="New reminder 1", trigger_offset="-PT30M", sent=False),
        ReminderCreateSchema(event_id=2, description="New reminder 2", trigger_offset="-PT1H", sent=False),
    ]

    result = await reminder_repository.create_many(create_data)

    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0] == ReminderResponse.from_model(
        Reminder(event_id=1, description="New reminder 1", trigger_offset="-PT30M", sent=False)
    )
    assert result[1] == ReminderResponse.from_model(
        Reminder(event_id=2, description="New reminder 2", trigger_offset="-PT1H", sent=False)
    )
    mock_session.add.assert_called()
    assert mock_session.add.call_count == 2
    assert mock_session.flush.call_count == 2


@pytest.mark.asyncio
async def test_create_creates_reminder_with_minimal_data(
    reminder_repository: ReminderRepository, mock_session: AsyncMock
) -> None:
    """Test that create creates reminder with minimal required data."""
    create_data = ReminderCreateSchema(
        event_id=1,
        description="New reminder",
        trigger_offset="-PT30M",
        sent=False,
    )

    result = await reminder_repository.create_one(create_data)

    assert result == ReminderResponse.from_model(
        Reminder(event_id=1, description="New reminder", trigger_offset="-PT30M", sent=False)
    )
    mock_session.add.assert_called_once()
    mock_session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_update_updates_existing_reminder(
    reminder_repository: ReminderRepository, mock_session: AsyncMock, sample_reminder: Reminder
) -> None:
    """Test that update_by_id updates an existing reminder."""
    mock_session.get.return_value = sample_reminder
    update_data = ReminderUpdateSchema(description="Updated reminder", trigger_offset="-PT1H", sent=True)

    result = await reminder_repository.update_by_id(1, update_data)

    assert result == ReminderResponse.from_model(
        Reminder(id=1, event_id=1, description="Updated reminder", trigger_offset="-PT1H", sent=True)
    )
    mock_session.get.assert_called_once_with(Reminder, 1)
    mock_session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_update_updates_multiple_fields(
    reminder_repository: ReminderRepository, mock_session: AsyncMock, sample_reminder: Reminder
) -> None:
    """Test that update can update multiple fields."""
    mock_session.get.return_value = sample_reminder
    update_data = ReminderUpdateSchema(
        description="Updated description",
        trigger_offset="-PT1H",
        sent=True,
    )

    result = await reminder_repository.update_by_id(1, update_data)

    assert result.description == "Updated description"
    assert result.trigger_offset == "-PT1H"
    assert result.sent is True
    mock_session.get.assert_called_once_with(Reminder, 1)
    mock_session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_update_raises_error_when_reminder_not_found(
    reminder_repository: ReminderRepository, mock_session: AsyncMock
) -> None:
    """Test that update_by_id raises ReminderNotFoundError when reminder not found."""
    mock_session.get.return_value = None
    update_data = ReminderUpdateSchema(description="Updated reminder", trigger_offset="-PT1H", sent=True)

    with pytest.raises(ReminderNotFoundError) as exc_info:
        await reminder_repository.update_by_id(999, update_data)

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
    update_data = ReminderUpdateSchema(sent=True)

    result = await reminder_repository.update_by_id(1, update_data)

    assert result.description == original_description  # Not changed
    assert result.trigger_offset == original_trigger_offset  # Not changed
    assert result.sent is True  # Changed
    mock_session.get.assert_called_once_with(Reminder, 1)
    mock_session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_find_returns_reminder_by_event_id(
    reminder_repository: ReminderRepository, mock_session: AsyncMock, sample_reminder: Reminder
) -> None:
    """Test that find returns reminder when found by event_id."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [sample_reminder]
    mock_session.execute.return_value = mock_result

    result = await reminder_repository.find(ReminderFilter(event_id=1))

    assert result == [ReminderResponse.from_model(sample_reminder)]
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_find_returns_none_when_not_found(
    reminder_repository: ReminderRepository, mock_session: AsyncMock
) -> None:
    """Test that find returns None when reminder not found by event_id."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute.return_value = mock_result

    result = await reminder_repository.find(ReminderFilter(event_id=999))

    assert result == []
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_delete_deletes_reminder(
    reminder_repository: ReminderRepository, mock_session: AsyncMock, sample_reminder: Reminder
) -> None:
    """Test that delete deletes an existing reminder."""
    mock_session.get.return_value = sample_reminder

    await reminder_repository.delete_by_id(1)

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
        await reminder_repository.delete_by_id(999)

    assert exc_info.value.reminder_id == 999
    mock_session.get.assert_called_once_with(Reminder, 999)
    mock_session.delete.assert_not_called()
    mock_session.flush.assert_not_called()
