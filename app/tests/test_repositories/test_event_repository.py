"""Tests for EventRepository using mocks."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, call

import pytest

from models.event import Event
from repositories.event_repository import EventRepository
from repositories.exceptions import EventNotFoundError
from repositories.schemas import EventCreateSchema, EventFilter, EventUpdateSchema


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
def event_repository(mock_session: AsyncMock) -> EventRepository:
    """Create an EventRepository instance with mocked session."""
    return EventRepository(mock_session)


@pytest.fixture
def sample_event() -> Event:
    """Create a sample Event instance for testing."""
    start_time = datetime(2025, 1, 1, 10, 0, tzinfo=UTC)
    end_time = datetime(2025, 1, 1, 11, 0, tzinfo=UTC)
    event = Event(
        user_id=12345,
        date_start=start_time,
        date_end=end_time,
        title="Test Event",
    )
    # Set id manually for testing (normally set by database)
    event.id = 1
    return event


@pytest.mark.asyncio
async def test_get_by_id_returns_event(
    event_repository: EventRepository, mock_session: AsyncMock, sample_event: Event
) -> None:
    """Test that get_by_id returns event when found."""
    mock_session.get.return_value = sample_event

    result = await event_repository.get_by_id(1)

    assert result is sample_event
    mock_session.get.assert_called_once_with(Event, 1)


@pytest.mark.asyncio
async def test_get_by_id_returns_none_when_not_found(
    event_repository: EventRepository, mock_session: AsyncMock
) -> None:
    """Test that get_by_id returns None when event not found."""
    mock_session.get.return_value = None

    result = await event_repository.get_by_id(999)

    assert result is None
    mock_session.get.assert_called_once_with(Event, 999)


@pytest.mark.asyncio
async def test_create_creates_event(event_repository: EventRepository, mock_session: AsyncMock) -> None:
    """Test that create creates a new event."""
    start_time = datetime(2025, 1, 1, 10, 0, tzinfo=UTC)
    end_time = datetime(2025, 1, 1, 11, 0, tzinfo=UTC)
    create_data = [
        EventCreateSchema(  # type: ignore[call-arg]
            user_id=12345,
            date_start=start_time,
            date_end=end_time,
            title="New Event",
        )
    ]

    result = await event_repository.create(create_data)

    assert len(result) == 1
    assert isinstance(result[0], Event)
    assert result[0].user_id == 12345
    assert result[0].date_start == start_time
    assert result[0].date_end == end_time
    assert result[0].title == "New Event"
    mock_session.add.assert_called_once_with(result[0])
    mock_session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_create_creates_multiple_events(event_repository: EventRepository, mock_session: AsyncMock) -> None:
    """Test that create creates multiple events."""
    start_time1 = datetime(2025, 1, 1, 10, 0, tzinfo=UTC)
    end_time1 = datetime(2025, 1, 1, 11, 0, tzinfo=UTC)
    start_time2 = datetime(2025, 1, 2, 10, 0, tzinfo=UTC)
    end_time2 = datetime(2025, 1, 2, 11, 0, tzinfo=UTC)
    create_data = [
        EventCreateSchema(user_id=12345, date_start=start_time1, date_end=end_time1, title="Event 1"),  # type: ignore[call-arg]
        EventCreateSchema(user_id=12345, date_start=start_time2, date_end=end_time2, title="Event 2"),  # type: ignore[call-arg]
    ]

    result = await event_repository.create(create_data)

    assert isinstance(result, list)
    assert len(result) == 2
    assert isinstance(result[0], Event)
    assert result[0].title == "Event 1"
    assert isinstance(result[1], Event)
    assert result[1].title == "Event 2"
    mock_session.add.assert_has_calls([call(result[0]), call(result[1])], any_order=True)
    assert mock_session.flush.call_count == 2


@pytest.mark.asyncio
async def test_create_creates_event_with_all_fields(event_repository: EventRepository, mock_session: AsyncMock) -> None:
    """Test that create creates event with all optional fields."""
    start_time = datetime(2025, 1, 1, 10, 0, tzinfo=UTC)
    end_time = datetime(2025, 1, 1, 11, 0, tzinfo=UTC)
    rdate_list = [datetime(2025, 1, 2, 10, 0, tzinfo=UTC)]
    exdate_list = [datetime(2025, 1, 3, 10, 0, tzinfo=UTC)]
    create_data = [
        EventCreateSchema(  # type: ignore[call-arg]
            user_id=12345,
            uid="event-123",
            calendar_id=1,
            date_start=start_time,
            date_end=end_time,
            all_day=True,
            need_to_remind=False,
            title="Full Event",
            description="Event description",
            rrule="FREQ=DAILY;COUNT=10",
            rdate=rdate_list,
            exdate=exdate_list,
        )
    ]

    result = await event_repository.create(create_data)

    assert len(result) == 1
    event = result[0]
    assert event.user_id == 12345
    assert event.uid == "event-123"
    assert event.calendar_id == 1
    assert event.all_day is True
    assert event.need_to_remind is False
    assert event.title == "Full Event"
    assert event.description == "Event description"
    assert event.rrule == "FREQ=DAILY;COUNT=10"
    assert event.rdate == rdate_list
    assert event.exdate == exdate_list


@pytest.mark.asyncio
async def test_update_updates_existing_event(
    event_repository: EventRepository, mock_session: AsyncMock, sample_event: Event
) -> None:
    """Test that update updates an existing event."""
    mock_session.get.return_value = sample_event
    update_data = EventUpdateSchema(title="Updated Event")  # type: ignore[call-arg]

    result = await event_repository.update(1, update_data)

    assert result is sample_event
    assert result.title == "Updated Event"
    mock_session.get.assert_called_once_with(Event, 1)
    mock_session.flush.assert_called_once()
    mock_session.refresh.assert_called_once_with(sample_event)


@pytest.mark.asyncio
async def test_update_updates_multiple_fields(
    event_repository: EventRepository, mock_session: AsyncMock, sample_event: Event
) -> None:
    """Test that update can update multiple fields."""
    mock_session.get.return_value = sample_event
    update_data = EventUpdateSchema(  # type: ignore[call-arg]
        title="Updated Title", description="Updated Description", all_day=True
    )

    result = await event_repository.update(1, update_data)

    assert result.title == "Updated Title"
    assert result.description == "Updated Description"
    assert result.all_day is True


@pytest.mark.asyncio
async def test_update_raises_error_when_event_not_found(
    event_repository: EventRepository, mock_session: AsyncMock
) -> None:
    """Test that update raises EventNotFoundError when event not found."""
    mock_session.get.return_value = None
    update_data = EventUpdateSchema(title="Updated Event")  # type: ignore[call-arg]

    with pytest.raises(EventNotFoundError) as exc_info:
        await event_repository.update(999, update_data)

    assert exc_info.value.event_id == 999
    mock_session.get.assert_called_once_with(Event, 999)
    mock_session.flush.assert_not_called()


@pytest.mark.asyncio
async def test_update_only_updates_provided_fields(
    event_repository: EventRepository, mock_session: AsyncMock, sample_event: Event
) -> None:
    """Test that update only updates fields provided in schema."""
    original_title = sample_event.title
    original_description = sample_event.description
    mock_session.get.return_value = sample_event
    update_data = EventUpdateSchema(need_to_remind=False)  # type: ignore[call-arg]

    result = await event_repository.update(1, update_data)

    assert result.title == original_title  # Not changed
    assert result.description == original_description  # Not changed
    assert result.need_to_remind is False  # Changed


@pytest.mark.asyncio
async def test_delete_deletes_event(
    event_repository: EventRepository, mock_session: AsyncMock, sample_event: Event
) -> None:
    """Test that delete deletes an existing event."""
    mock_session.get.return_value = sample_event

    await event_repository.delete(1)

    mock_session.get.assert_called_once_with(Event, 1)
    mock_session.delete.assert_called_once_with(sample_event)
    mock_session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_delete_raises_error_when_event_not_found(
    event_repository: EventRepository, mock_session: AsyncMock
) -> None:
    """Test that delete raises EventNotFoundError when event not found."""
    mock_session.get.return_value = None

    with pytest.raises(EventNotFoundError) as exc_info:
        await event_repository.delete(999)

    assert exc_info.value.event_id == 999
    mock_session.get.assert_called_once_with(Event, 999)
    mock_session.delete.assert_not_called()


@pytest.mark.asyncio
async def test_find_returns_all_events_without_filters(
    event_repository: EventRepository, mock_session: AsyncMock
) -> None:
    """Test that find returns all events when no filters are provided."""
    start_time = datetime(2025, 1, 1, 10, 0, tzinfo=UTC)
    end_time = datetime(2025, 1, 1, 11, 0, tzinfo=UTC)
    events = [
        Event(user_id=12345, date_start=start_time, date_end=end_time, title="Event 1"),
        Event(user_id=12345, date_start=start_time, date_end=end_time, title="Event 2"),
    ]
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = events
    mock_session.execute.return_value = mock_result
    filter_data = EventFilter()  # type: ignore[call-arg]

    result = await event_repository.find(filter_data)

    assert len(result) == 2
    assert result == events
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_find_filters_by_user_id(event_repository: EventRepository, mock_session: AsyncMock) -> None:
    """Test that find filters events by user_id."""
    start_time = datetime(2025, 1, 1, 10, 0, tzinfo=UTC)
    end_time = datetime(2025, 1, 1, 11, 0, tzinfo=UTC)
    events = [
        Event(user_id=12345, date_start=start_time, date_end=end_time, title="Event 1"),
    ]
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = events
    mock_session.execute.return_value = mock_result
    filter_data = EventFilter(user_id=12345)  # type: ignore[call-arg]

    result = await event_repository.find(filter_data)

    assert len(result) == 1
    assert result[0].user_id == 12345
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_find_filters_by_uid(event_repository: EventRepository, mock_session: AsyncMock) -> None:
    """Test that find filters events by uid."""
    start_time = datetime(2025, 1, 1, 10, 0, tzinfo=UTC)
    end_time = datetime(2025, 1, 1, 11, 0, tzinfo=UTC)
    events = [
        Event(
            user_id=12345,
            uid="event-123",
            date_start=start_time,
            date_end=end_time,
            title="Event 1",
        ),
    ]
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = events
    mock_session.execute.return_value = mock_result
    filter_data = EventFilter(uid="event-123")  # type: ignore[call-arg]

    result = await event_repository.find(filter_data)

    assert len(result) == 1
    assert result[0].uid == "event-123"
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_find_filters_by_calendar_id(event_repository: EventRepository, mock_session: AsyncMock) -> None:
    """Test that find filters events by calendar_id."""
    start_time = datetime(2025, 1, 1, 10, 0, tzinfo=UTC)
    end_time = datetime(2025, 1, 1, 11, 0, tzinfo=UTC)
    events = [
        Event(
            user_id=12345,
            calendar_id=1,
            date_start=start_time,
            date_end=end_time,
            title="Event 1",
        ),
    ]
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = events
    mock_session.execute.return_value = mock_result
    filter_data = EventFilter(calendar_id=1)  # type: ignore[call-arg]

    result = await event_repository.find(filter_data)

    assert len(result) == 1
    assert result[0].calendar_id == 1
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_find_filters_by_start_date_from(event_repository: EventRepository, mock_session: AsyncMock) -> None:
    """Test that find filters events by start_date_from."""
    start_time = datetime(2025, 1, 1, 10, 0, tzinfo=UTC)
    end_time = datetime(2025, 1, 1, 11, 0, tzinfo=UTC)
    events = [
        Event(user_id=12345, date_start=start_time, date_end=end_time, title="Event 1"),
    ]
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = events
    mock_session.execute.return_value = mock_result
    filter_data = EventFilter(start_date_from=datetime(2025, 1, 1, 0, 0, tzinfo=UTC))  # type: ignore[call-arg]

    result = await event_repository.find(filter_data)

    assert len(result) == 1
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_find_filters_by_start_date_to(event_repository: EventRepository, mock_session: AsyncMock) -> None:
    """Test that find filters events by start_date_to."""
    start_time = datetime(2025, 1, 1, 10, 0, tzinfo=UTC)
    end_time = datetime(2025, 1, 1, 11, 0, tzinfo=UTC)
    events = [
        Event(user_id=12345, date_start=start_time, date_end=end_time, title="Event 1"),
    ]
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = events
    mock_session.execute.return_value = mock_result
    filter_data = EventFilter(start_date_to=datetime(2025, 1, 31, 23, 59, tzinfo=UTC))  # type: ignore[call-arg]

    result = await event_repository.find(filter_data)

    assert len(result) == 1
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_find_applies_multiple_filters(event_repository: EventRepository, mock_session: AsyncMock) -> None:
    """Test that find can apply multiple filters simultaneously."""
    start_time = datetime(2025, 1, 1, 10, 0, tzinfo=UTC)
    end_time = datetime(2025, 1, 1, 11, 0, tzinfo=UTC)
    events = [
        Event(
            user_id=12345,
            calendar_id=1,
            date_start=start_time,
            date_end=end_time,
            title="Event 1",
        ),
    ]
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = events
    mock_session.execute.return_value = mock_result
    filter_data = EventFilter(  # type: ignore[call-arg]
        user_id=12345, calendar_id=1, start_date_from=datetime(2025, 1, 1, 0, 0, tzinfo=UTC)
    )

    result = await event_repository.find(filter_data)

    assert len(result) == 1
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_find_applies_limit_and_offset(event_repository: EventRepository, mock_session: AsyncMock) -> None:
    """Test that find applies limit and offset to the query."""
    start_time = datetime(2025, 1, 1, 10, 0, tzinfo=UTC)
    end_time = datetime(2025, 1, 1, 11, 0, tzinfo=UTC)
    events = [
        Event(user_id=12345, date_start=start_time, date_end=end_time, title="Event 2"),
    ]
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = events
    mock_session.execute.return_value = mock_result
    filter_data = EventFilter(limit=10, offset=5)  # type: ignore[call-arg]

    result = await event_repository.find(filter_data)

    assert len(result) == 1
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_find_returns_empty_list_when_no_matches(
    event_repository: EventRepository, mock_session: AsyncMock
) -> None:
    """Test that find returns empty list when no events match filters."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute.return_value = mock_result
    filter_data = EventFilter(user_id=99999)  # type: ignore[call-arg]

    result = await event_repository.find(filter_data)

    assert result == []
    mock_session.execute.assert_called_once()
