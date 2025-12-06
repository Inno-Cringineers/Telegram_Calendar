"""Tests for CalendarRepository using mocks."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from models.calendar import Calendar
from repositories.calendar_repository import CalendarRepository
from repositories.exceptions import CalendarNotFoundError
from repositories.schemas import CalendarCreateSchema, CalendarFilter, CalendarResponse, CalendarUpdateSchema


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
def calendar_repository(mock_session: AsyncMock) -> CalendarRepository:
    """Create a CalendarRepository instance with mocked session."""
    return CalendarRepository(mock_session)


@pytest.fixture
def sample_calendar() -> Calendar:
    """Create a sample Calendar instance for testing."""
    calendar = Calendar(
        user_id=12345,
        name="Test Calendar",
        url="https://example.com/calendar.ics",
        last_sync=None,
        sync_enabled=True,
    )
    # Set id manually for testing (normally set by database)
    calendar.id = 1
    return calendar


@pytest.mark.asyncio
async def test_get_by_id_returns_calendar(
    calendar_repository: CalendarRepository, mock_session: AsyncMock, sample_calendar: Calendar
) -> None:
    """Test that get_by_id returns calendar when found."""
    mock_session.get.return_value = sample_calendar

    result = await calendar_repository.get_by_id(1)

    assert result == CalendarResponse.from_model(sample_calendar)
    mock_session.get.assert_called_once_with(Calendar, 1)


@pytest.mark.asyncio
async def test_get_by_id_returns_none_when_not_found(
    calendar_repository: CalendarRepository, mock_session: AsyncMock
) -> None:
    """Test that get_by_id returns None when calendar not found."""
    mock_session.get.return_value = None

    result = await calendar_repository.get_by_id(999)

    assert result is None
    mock_session.get.assert_called_once_with(Calendar, 999)


@pytest.mark.asyncio
async def test_create_creates_calendar(calendar_repository: CalendarRepository, mock_session: AsyncMock) -> None:
    """Test that create_one creates a new calendar."""
    result = await calendar_repository.create_one(
        CalendarCreateSchema(user_id=12345, name="New Calendar", url="https://example.com/new.ics")
    )

    assert result.user_id == 12345
    assert result.name == "New Calendar"
    assert result.url == "https://example.com/new.ics"
    mock_session.add.assert_called_once()
    mock_session.flush.assert_called_once()
    mock_session.refresh.assert_called_once()


@pytest.mark.asyncio
async def test_update_by_id_updates_existing_calendar(
    calendar_repository: CalendarRepository, mock_session: AsyncMock, sample_calendar: Calendar
) -> None:
    """Test that update_by_id updates an existing calendar."""
    mock_session.get.return_value = sample_calendar
    update_data = CalendarUpdateSchema(name="Updated Calendar")  # type: ignore[call-arg]

    result = await calendar_repository.update_by_id(1, update_data)

    assert result == CalendarResponse.from_model(sample_calendar)
    assert result.name == "Updated Calendar"
    mock_session.get.assert_called_once_with(Calendar, 1)
    mock_session.flush.assert_called_once()
    mock_session.refresh.assert_called_once()


@pytest.mark.asyncio
async def test_update_updates_multiple_fields(
    calendar_repository: CalendarRepository, mock_session: AsyncMock, sample_calendar: Calendar
) -> None:
    """Test that update can update multiple fields."""
    mock_session.get.return_value = sample_calendar
    update_data = CalendarUpdateSchema(name="Updated Name", sync_enabled=False)

    result = await calendar_repository.update_by_id(1, update_data)

    assert result == CalendarResponse.from_model(sample_calendar)
    assert result.name == "Updated Name"
    assert result.sync_enabled is False
    mock_session.get.assert_called_once_with(Calendar, 1)
    mock_session.flush.assert_called_once()
    mock_session.refresh.assert_called_once()


@pytest.mark.asyncio
async def test_update_raises_error_when_calendar_not_found(
    calendar_repository: CalendarRepository, mock_session: AsyncMock
) -> None:
    """Test that update raises CalendarNotFoundError when calendar not found."""
    mock_session.get.return_value = None
    update_data = CalendarUpdateSchema(name="Updated Calendar")

    with pytest.raises(CalendarNotFoundError) as exc_info:
        await calendar_repository.update_by_id(999, update_data)

    assert exc_info.value.calendar_id == 999
    mock_session.get.assert_called_once_with(Calendar, 999)
    mock_session.flush.assert_not_called()


@pytest.mark.asyncio
async def test_update_only_updates_provided_fields(
    calendar_repository: CalendarRepository, mock_session: AsyncMock, sample_calendar: Calendar
) -> None:
    """Test that update only updates fields provided in schema."""
    original_name = sample_calendar.name
    original_url = sample_calendar.url
    mock_session.get.return_value = sample_calendar
    update_data = CalendarUpdateSchema(sync_enabled=False)  # type: ignore[call-arg]

    result = await calendar_repository.update_by_id(1, update_data)

    assert result == CalendarResponse.from_model(sample_calendar)
    assert result.name == original_name  # Not changed
    assert result.url == original_url  # Not changed
    assert result.sync_enabled is False


@pytest.mark.asyncio
async def test_delete_deletes_calendar(
    calendar_repository: CalendarRepository, mock_session: AsyncMock, sample_calendar: Calendar
) -> None:
    """Test that delete deletes an existing calendar."""
    mock_session.get.return_value = sample_calendar

    await calendar_repository.delete_by_id(1)

    mock_session.get.assert_called_once_with(Calendar, 1)
    mock_session.delete.assert_called_once_with(sample_calendar)
    mock_session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_delete_raises_error_when_calendar_not_found(
    calendar_repository: CalendarRepository, mock_session: AsyncMock
) -> None:
    """Test that delete raises CalendarNotFoundError when calendar not found."""
    mock_session.get.return_value = None

    with pytest.raises(CalendarNotFoundError) as exc_info:
        await calendar_repository.delete_by_id(999)

    assert exc_info.value.calendar_id == 999
    mock_session.get.assert_called_once_with(Calendar, 999)
    mock_session.delete.assert_not_called()


@pytest.mark.asyncio
async def test_find_returns_all_calendars_without_filters(
    calendar_repository: CalendarRepository, mock_session: AsyncMock
) -> None:
    """Test that find returns all calendars when no filters are provided."""
    calendars = [
        Calendar(user_id=12345, name="Calendar 1", url="https://example.com/1.ics", sync_enabled=True),
        Calendar(user_id=12345, name="Calendar 2", url="https://example.com/2.ics", sync_enabled=True),
    ]
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = calendars
    mock_session.execute.return_value = mock_result
    filter_data = CalendarFilter()

    result = await calendar_repository.find(filter_data)

    assert len(result) == 2
    assert result == [CalendarResponse.from_model(calendar) for calendar in calendars]
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_find_filters_by_user_id(calendar_repository: CalendarRepository, mock_session: AsyncMock) -> None:
    """Test that find filters calendars by user_id."""
    calendars = [
        Calendar(user_id=12345, name="Calendar 1", url="https://example.com/1.ics", sync_enabled=True),
    ]
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = calendars
    mock_session.execute.return_value = mock_result
    filter_data = CalendarFilter(user_id=12345)

    result = await calendar_repository.find(filter_data)

    assert len(result) == 1
    assert result[0] == CalendarResponse.from_model(calendars[0])
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_find_filters_by_name(calendar_repository: CalendarRepository, mock_session: AsyncMock) -> None:
    """Test that find filters calendars by name."""
    calendars = [
        Calendar(user_id=12345, name="My Calendar", url="https://example.com/1.ics", sync_enabled=True),
    ]
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = calendars
    mock_session.execute.return_value = mock_result
    filter_data = CalendarFilter(name="My Calendar")

    result = await calendar_repository.find(filter_data)

    assert len(result) == 1
    assert result[0].name == "My Calendar"
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_find_filters_by_url(calendar_repository: CalendarRepository, mock_session: AsyncMock) -> None:
    """Test that find filters calendars by url."""
    calendars = [
        Calendar(user_id=12345, name="Calendar 1", url="https://example.com/specific.ics", sync_enabled=True),
    ]
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = calendars
    mock_session.execute.return_value = mock_result
    filter_data = CalendarFilter(url="https://example.com/specific.ics")

    result = await calendar_repository.find(filter_data)

    assert len(result) == 1
    assert result[0].url == "https://example.com/specific.ics"
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_find_applies_multiple_filters(calendar_repository: CalendarRepository, mock_session: AsyncMock) -> None:
    """Test that find can apply multiple filters simultaneously."""
    calendars = [
        Calendar(user_id=12345, name="My Calendar", url="https://example.com/1.ics", sync_enabled=True),
    ]
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = calendars
    mock_session.execute.return_value = mock_result
    filter_data = CalendarFilter(user_id=12345, name="My Calendar", url="https://example.com/1.ics")

    result = await calendar_repository.find(filter_data)

    assert len(result) == 1
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_find_returns_empty_list_when_no_matches(
    calendar_repository: CalendarRepository, mock_session: AsyncMock
) -> None:
    """Test that find returns empty list when no calendars match filters."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute.return_value = mock_result
    filter_data = CalendarFilter(user_id=99999)

    result = await calendar_repository.find(filter_data)

    assert result == []
    mock_session.execute.assert_called_once()
