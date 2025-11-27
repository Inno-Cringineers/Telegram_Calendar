"""
Unit tests for EventRepository using TDD approach.

Tests cover:
- Creating events
- Retrieving events by ID
- Retrieving events by user_id
- Retrieving events by date range
- Updating events
- Deleting events
- Getting upcoming events for reminders
- Filtering events with EventFilter
"""

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import pytest
import pytest_asyncio
from sqlalchemy import select, text

from database.database import Base, get_engine, get_session_maker
from models.calendar import Calendar
from models.event import Event
from models.reminder import Reminder
from repositories.exceptions import EventNotFoundError
from repositories.schemas import EventCreateSchema, EventFilter, EventUpdateSchema

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from models.settings import Settings
    from repositories.event_repository import EventRepository


@pytest_asyncio.fixture
async def engine():
    """Create an async engine and ensure tables are created for tests."""
    # Import all models to ensure they are registered in Base.metadata
    # These imports are needed for side effects (SQLAlchemy table registration)
    from models.calendar import Calendar  # noqa: F401  # pyright: ignore[reportUnusedImport]
    from models.event import Event  # noqa: F401  # pyright: ignore[reportUnusedImport]
    from models.reminder import Reminder  # noqa: F401  # pyright: ignore[reportUnusedImport]
    from models.settings import Settings  # noqa: F401  # pyright: ignore[reportUnusedImport]

    engine = get_engine("sqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Enable foreign keys for SQLite
        await conn.run_sync(lambda sync_conn: sync_conn.execute(text("PRAGMA foreign_keys=ON;")))
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def session_maker(engine):
    """Create session maker for tests."""
    return get_session_maker(engine)


@pytest_asyncio.fixture
async def session(session_maker: "async_sessionmaker[AsyncSession]"):
    """Create a test session."""
    async with session_maker() as session:
        yield session


@pytest_asyncio.fixture
async def repository(session: "AsyncSession") -> "EventRepository":
    """Create EventRepository instance for tests.

    Note: Repository receives session directly, not through Store.
    This is the recommended approach - simple and explicit.
    """
    from repositories.event_repository import EventRepository

    return EventRepository(session)


@pytest_asyncio.fixture
async def test_user_settings(session: "AsyncSession"):
    """Create test user settings."""
    from models.settings import Settings

    settings = Settings(
        user_id=1,
        timezone="UTC+2",
        language="ru",
        default_reminder_offset=15 * 60,  # 15 minutes
    )
    session.add(settings)
    await session.commit()
    return settings


# ============================================================================
# CREATE OPERATIONS
# ============================================================================


@pytest.mark.asyncio
async def test_create_event_success(repository: "EventRepository") -> None:
    """Test successful event creation."""
    # Arrange
    event_data = EventCreateSchema(
        user_id=1,
        title="Test Event",
        date_start=datetime.now(UTC),
        date_end=datetime.now(UTC) + timedelta(hours=1),
        reminder_offset=15 * 60,
        need_to_remind=True,
        description=None,
        rrule=None,
        calendar_id=None,
    )

    # Act
    event = await repository.create(event_data)

    # Assert
    assert event.id is not None
    assert event.title == "Test Event"
    assert event.user_id == 1

    # check if reminder created
    stmt = select(Reminder).where(Reminder.event_id == event.id)
    result = await repository.session.execute(stmt)
    reminder = result.scalar_one_or_none()
    assert reminder is not None
    assert reminder.event_id == event.id
    assert reminder.user_id == 1
    assert reminder.remind_at == event.date_start - timedelta(seconds=event.reminder_offset)
    assert reminder.sent is False


@pytest.mark.asyncio
async def test_create_event_with_default_reminder_offset(
    repository: "EventRepository", test_user_settings: "Settings"
) -> None:
    """Test event creation with default reminder offset from settings."""
    # Arrange
    event_data = EventCreateSchema(
        user_id=1,
        title="Test Event",
        date_start=datetime.now(UTC),
        date_end=datetime.now(UTC) + timedelta(hours=1),
        reminder_offset=None,  # Not provided - should use default from settings
        need_to_remind=True,
        description=None,
        rrule=None,
        calendar_id=None,
    )

    # Act
    event = await repository.create(event_data)

    # Assert
    assert event.reminder_offset == test_user_settings.default_reminder_offset


@pytest.mark.asyncio
async def test_create_event_with_calendar_id(repository: "EventRepository", session: "AsyncSession") -> None:
    """Test event creation with calendar_id."""
    # Arrange
    calendar = Calendar(user_id=1, name="Work", url="http://example.com/work.ics")
    session.add(calendar)
    await session.flush()

    event_data = EventCreateSchema(
        user_id=1,
        title="Work Event",
        date_start=datetime.now(UTC),
        date_end=datetime.now(UTC) + timedelta(hours=1),
        reminder_offset=15 * 60,
        need_to_remind=True,
        description=None,
        rrule=None,
        calendar_id=calendar.id,
    )

    # Act
    event = await repository.create(event_data)

    # Assert
    assert event.calendar_id == calendar.id


# ============================================================================
# READ OPERATIONS
# ============================================================================


@pytest.mark.asyncio
async def test_get_by_id_success(repository: "EventRepository", session: "AsyncSession") -> None:
    """Test retrieving event by ID."""
    # Arrange
    event = Event(
        user_id=1,
        title="Test Event",
        date_start=datetime.now(UTC),
        date_end=datetime.now(UTC) + timedelta(hours=1),
        reminder_offset=15 * 60,
    )
    session.add(event)
    await session.flush()
    event_id = event.id

    # Act
    retrieved = await repository.get_by_id(event_id)

    # Assert
    assert retrieved is not None
    assert retrieved.id == event_id
    assert retrieved.title == "Test Event"


@pytest.mark.asyncio
async def test_get_by_id_not_found(repository: "EventRepository") -> None:
    """Test retrieving non-existent event by ID."""
    # Arrange
    non_existent_id = 999

    # Act
    result = await repository.get_by_id(non_existent_id)

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_by_user_id(repository: "EventRepository", session: "AsyncSession") -> None:
    """Test retrieving all events for a user."""
    # Arrange
    event1 = Event(
        user_id=1,
        title="Event 1",
        date_start=datetime.now(UTC),
        date_end=datetime.now(UTC) + timedelta(hours=1),
        reminder_offset=15 * 60,
    )
    event2 = Event(
        user_id=1,
        title="Event 2",
        date_start=datetime.now(UTC),
        date_end=datetime.now(UTC) + timedelta(hours=1),
        reminder_offset=15 * 60,
    )
    event3 = Event(
        user_id=2,  # Different user
        title="Event 3",
        date_start=datetime.now(UTC),
        date_end=datetime.now(UTC) + timedelta(hours=1),
        reminder_offset=15 * 60,
    )
    session.add_all([event1, event2, event3])
    await session.flush()

    # Act
    events = await repository.get_by_user_id(1)

    # Assert
    assert len(events) == 2
    assert all(e.user_id == 1 for e in events)


@pytest.mark.asyncio
async def test_get_by_user_id_empty(repository: "EventRepository") -> None:
    """Test retrieving events for user with no events."""
    # Arrange
    user_id = 1

    # Act
    events = await repository.get_by_user_id(user_id)

    # Assert
    assert events == []


@pytest.mark.asyncio
async def test_get_by_date_range(repository: "EventRepository", session: "AsyncSession") -> None:
    """Test retrieving events within a date range using EventFilter."""
    # Arrange
    now = datetime.now(UTC)
    past_start = now - timedelta(days=2)
    past_event = Event(
        user_id=1,
        title="Past Event",
        date_start=past_start,
        date_end=past_start + timedelta(hours=1),  # Ensure date_end >= date_start
        reminder_offset=15 * 60,
    )
    current_event = Event(
        user_id=1,
        title="Current Event",
        date_start=now,
        date_end=now + timedelta(hours=1),
        reminder_offset=15 * 60,
    )
    future_event = Event(
        user_id=1,
        title="Future Event",
        date_start=now + timedelta(days=2),
        date_end=now + timedelta(days=2, hours=1),
        reminder_offset=15 * 60,
    )
    session.add_all([past_event, current_event, future_event])
    await session.flush()

    filter = EventFilter(
        user_id=1,
        start_date_from=now - timedelta(days=1),
        start_date_to=now + timedelta(days=1),
        calendar_id=None,
        need_to_remind=None,
        limit=100,
        offset=0,
    )

    # Act
    events = await repository.find(filter)

    # Assert
    assert len(events) == 1
    assert events[0].title == "Current Event"


@pytest.mark.asyncio
async def test_get_upcoming_events(repository: "EventRepository", session: "AsyncSession") -> None:
    """Test retrieving upcoming events for reminders."""
    # Arrange
    now = datetime.now(UTC)
    past_event = EventCreateSchema(
        user_id=1,
        title="Past Event",
        date_start=now - timedelta(hours=1),
        date_end=now,
        reminder_offset=15 * 60,
        need_to_remind=True,
        description=None,
        rrule=None,
        calendar_id=None,
    )
    upcoming_event = EventCreateSchema(
        user_id=1,
        title="Upcoming Event",
        date_start=now + timedelta(hours=1),
        date_end=now + timedelta(hours=2),
        reminder_offset=15 * 60,
        need_to_remind=True,
        description=None,
        rrule=None,
        calendar_id=None,
    )
    no_reminder_event = EventCreateSchema(
        user_id=1,
        title="No Reminder Event",
        date_start=now + timedelta(hours=5),
        date_end=now + timedelta(hours=6),
        reminder_offset=15 * 60,
        need_to_remind=False,
        description=None,
        rrule=None,
        calendar_id=None,
    )

    past_event = await repository.create(past_event)
    await repository.create(upcoming_event)
    await repository.create(no_reminder_event)
    await repository.session.flush()
    await repository.set_reminder_sent(past_event.id)

    # Act
    events = await repository.get_upcoming_for_reminders(user_id=1, from_time=now, to_time=now + timedelta(hours=3))

    # Assert
    assert len(events) == 1
    assert events[0].title == "Upcoming Event"


# ============================================================================
# UPDATE OPERATIONS
# ============================================================================


@pytest.mark.asyncio
async def test_update_event_success(
    repository: "EventRepository", session: "AsyncSession", test_user_settings: "Settings"
) -> None:
    """Test successful event update."""
    # Arrange
    event = Event(
        user_id=1,
        title="Original Title",
        date_start=datetime.now(UTC),
        date_end=datetime.now(UTC) + timedelta(hours=1),
        reminder_offset=15 * 60,
    )
    session.add(event)
    await session.flush()
    event_id = event.id

    update_data = EventUpdateSchema(title="Updated Title", description="New description")  # type: ignore[call-arg]

    # Act
    updated = await repository.update(event_id, update_data)

    # Assert
    assert updated.title == "Updated Title"
    assert updated.description == "New description"
    assert updated.id == event_id


@pytest.mark.asyncio
async def test_update_event_not_found(repository: "EventRepository") -> None:
    """Test updating non-existent event."""
    # Arrange
    non_existent_id = 999
    update_data = EventUpdateSchema(title="New Title")  # type: ignore[call-arg]

    # Act & Assert
    with pytest.raises(EventNotFoundError):
        await repository.update(non_existent_id, update_data)


@pytest.mark.asyncio
async def test_update_event_partial(
    repository: "EventRepository", session: "AsyncSession", test_user_settings: "Settings"
) -> None:
    """Test partial event update (only some fields)."""
    # Arrange
    event = EventCreateSchema(
        user_id=1,
        title="Original Title",
        description="Original Description",
        date_start=datetime.now(UTC),
        date_end=datetime.now(UTC) + timedelta(hours=1),
        reminder_offset=15 * 60,
        need_to_remind=True,
        rrule=None,
        calendar_id=None,
    )
    event = await repository.create(event)

    update_data = EventUpdateSchema(title="Updated Title")  # type: ignore[call-arg]

    # Act
    updated = await repository.update(event.id, update_data)

    # Assert
    assert updated.title == "Updated Title"
    assert updated.description == "Original Description"  # Unchanged


# ============================================================================
# DELETE OPERATIONS
# ============================================================================


@pytest.mark.asyncio
async def test_delete_event_success(repository: "EventRepository") -> None:
    """Test successful event deletion."""
    # Arrange
    event = EventCreateSchema(
        user_id=1,
        title="Event to Delete",
        date_start=datetime.now(UTC),
        date_end=datetime.now(UTC) + timedelta(hours=1),
        reminder_offset=15 * 60,
        need_to_remind=True,
        description=None,
        rrule=None,
        calendar_id=None,
    )
    event = await repository.create(event)

    # Act
    await repository.delete(event.id)

    # Assert
    result = await repository.session.execute(select(Event).where(Event.id == event.id))
    assert result.scalar() is None


@pytest.mark.asyncio
async def test_delete_event_not_found(repository: "EventRepository") -> None:
    """Test deleting non-existent event."""
    # Arrange
    non_existent_id = 999

    # Act & Assert
    with pytest.raises(EventNotFoundError):
        await repository.delete(non_existent_id)


@pytest.mark.asyncio
async def test_delete_event_checks_user_ownership(repository: "EventRepository") -> None:
    """Test that deletion checks user ownership."""
    # Arrange
    event = EventCreateSchema(
        user_id=1,
        title="User 1 Event",
        date_start=datetime.now(UTC),
        date_end=datetime.now(UTC) + timedelta(hours=1),
        reminder_offset=15 * 60,
        need_to_remind=True,
        description=None,
        rrule=None,
        calendar_id=None,
    )
    event = await repository.create(event)

    # Act & Assert
    with pytest.raises(EventNotFoundError):
        await repository.delete(event.id, user_id=2)  # Different user


# ============================================================================
# EDGE CASES AND VALIDATION
# ============================================================================


@pytest.mark.asyncio
async def test_get_by_date_range_inclusive_boundaries(
    repository: "EventRepository", session: "AsyncSession", test_user_settings: "Settings"
) -> None:
    """Test that date range boundaries are inclusive using EventFilter."""
    # Arrange
    now = datetime.now(UTC)
    event_at_start = EventCreateSchema(
        user_id=1,
        title="Event at Start",
        date_start=now,
        date_end=now + timedelta(hours=1),
        reminder_offset=15 * 60,
        need_to_remind=True,
        description=None,
        rrule=None,
        calendar_id=None,
    )
    event_at_end = EventCreateSchema(
        user_id=1,
        title="Event at End",
        date_start=now + timedelta(days=1),
        date_end=now + timedelta(days=1, hours=1),
        reminder_offset=15 * 60,
        need_to_remind=True,
        description=None,
        rrule=None,
        calendar_id=None,
    )
    event_at_start = await repository.create(event_at_start)
    event_at_end = await repository.create(event_at_end)

    filter = EventFilter(
        user_id=1,
        start_date_from=now,
        start_date_to=now + timedelta(days=1),
        calendar_id=None,
        need_to_remind=None,
        limit=100,
        offset=0,
    )

    # Act
    events = await repository.find(filter)

    # Assert
    assert len(events) == 2


@pytest.mark.asyncio
async def test_get_upcoming_events_respects_need_to_remind(repository: "EventRepository") -> None:
    """Test that get_upcoming_for_reminders only returns events with need_to_remind=True."""
    # Arrange
    now = datetime.now(UTC)
    event_with_reminder = EventCreateSchema(
        user_id=1,
        title="With Reminder",
        date_start=now + timedelta(hours=1),
        date_end=now + timedelta(hours=2),
        reminder_offset=15 * 60,
        need_to_remind=True,
        description=None,
        rrule=None,
        calendar_id=None,
    )
    event_without_reminder = EventCreateSchema(
        user_id=1,
        title="Without Reminder",
        date_start=now + timedelta(hours=1),
        date_end=now + timedelta(hours=2),
        reminder_offset=15 * 60,
        need_to_remind=False,
        description=None,
        rrule=None,
        calendar_id=None,
    )
    event_with_reminder = await repository.create(event_with_reminder)
    event_without_reminder = await repository.create(event_without_reminder)

    # Act
    events = await repository.get_upcoming_for_reminders(user_id=1, from_time=now, to_time=now + timedelta(hours=3))

    # Assert
    assert len(events) == 1
    assert events[0].title == "With Reminder"


# ============================================================================
# FILTER OPERATIONS (find method)
# ============================================================================


@pytest.mark.asyncio
async def test_find_with_multiple_filters(repository: "EventRepository") -> None:
    """Test find() method with multiple filters combined."""
    # Arrange
    calendar = Calendar(user_id=1, name="Work", url="http://example.com/work.ics")
    repository.session.add(calendar)
    await repository.session.flush()
    calendar_id = await repository.session.scalar(select(Calendar.id).where(Calendar.user_id == 1))

    event1 = EventCreateSchema(
        user_id=1,
        title="Work Event",
        date_start=datetime.now(UTC),
        date_end=datetime.now(UTC) + timedelta(hours=1),
        reminder_offset=15 * 60,
        need_to_remind=True,
        description=None,
        rrule=None,
        calendar_id=calendar_id,
    )
    event2 = EventCreateSchema(
        user_id=1,
        title="Personal Event",
        date_start=datetime.now(UTC),
        date_end=datetime.now(UTC) + timedelta(hours=1),
        reminder_offset=15 * 60,
        need_to_remind=True,
        description=None,
        rrule=None,
        calendar_id=None,
    )
    event1 = await repository.create(event1)
    event2 = await repository.create(event2)

    filter = EventFilter(
        user_id=1,
        calendar_id=calendar.id,
        need_to_remind=True,
        start_date_from=None,
        start_date_to=None,
        limit=100,
        offset=0,
    )

    # Act
    events = await repository.find(filter)

    # Assert
    assert len(events) == 1
    assert events[0].title == "Work Event"


@pytest.mark.asyncio
async def test_find_with_pagination(repository: "EventRepository") -> None:
    """Test find() method with limit and offset."""
    # Arrange
    events = [
        EventCreateSchema(
            user_id=1,
            title=f"Event {i}",
            date_start=datetime.now(UTC) + timedelta(minutes=i),  # Different times for ordering
            date_end=datetime.now(UTC) + timedelta(hours=1, minutes=i),
            reminder_offset=15 * 60,
            need_to_remind=True,
            description=None,
            rrule=None,
            calendar_id=None,
        )
        for i in range(10)
    ]
    for event in events:
        await repository.create(event)

    filter = EventFilter(
        user_id=1,
        limit=5,
        offset=0,
        calendar_id=None,
        start_date_from=None,
        start_date_to=None,
        need_to_remind=None,
    )

    # Act
    first_page = await repository.find(filter)

    # Assert
    assert len(first_page) == 5

    # Arrange for second page
    filter = EventFilter(
        user_id=1,
        limit=5,
        offset=5,
        calendar_id=None,
        start_date_from=None,
        start_date_to=None,
        need_to_remind=None,
    )

    # Act
    second_page = await repository.find(filter)

    # Assert
    assert len(second_page) == 5
    assert first_page[0].id != second_page[0].id


@pytest.mark.asyncio
async def test_find_empty_result(repository: "EventRepository") -> None:
    """Test find() method with filters that match no events."""
    # Arrange
    filter = EventFilter(
        user_id=999,
        calendar_id=None,
        start_date_from=None,
        start_date_to=None,
        need_to_remind=None,
        limit=100,
        offset=0,
    )

    # Act
    events = await repository.find(filter)

    # Assert
    assert events == []


# ============================================================================
# EDGE CASES AND BOUNDARY CONDITIONS
# ============================================================================


@pytest.mark.asyncio
async def test_create_event_without_settings_fallback(repository: "EventRepository", session: "AsyncSession") -> None:
    """Test event creation without user settings - should use fallback (15 minutes)."""
    # Arrange
    event_data = EventCreateSchema(
        user_id=999,  # User without settings
        title="Test Event",
        date_start=datetime.now(UTC),
        date_end=datetime.now(UTC) + timedelta(hours=1),
        reminder_offset=None,
        need_to_remind=True,
        description=None,
        rrule=None,
        calendar_id=None,
    )

    # Act
    event = await repository.create(event_data)

    # Assert
    assert event.reminder_offset == 15 * 60  # Fallback: 15 minutes


@pytest.mark.asyncio
async def test_create_event_with_minimal_data(repository: "EventRepository", test_user_settings: "Settings") -> None:
    """Test event creation with minimal required data."""
    # Arrange
    event_data = EventCreateSchema(
        user_id=1,
        title="Minimal Event",
        date_start=datetime.now(UTC),
        date_end=datetime.now(UTC) + timedelta(hours=1),
        reminder_offset=None,
        need_to_remind=True,
        description=None,
        rrule=None,
        calendar_id=None,
    )

    # Act
    event = await repository.create(event_data)

    # Assert
    assert event.id is not None
    assert event.title == "Minimal Event"
    assert event.description is None
    assert event.rrule is None
    assert event.calendar_id is None


@pytest.mark.asyncio
async def test_create_event_with_maximal_data(
    repository: "EventRepository", session: "AsyncSession", test_user_settings: "Settings"
) -> None:
    """Test event creation with all fields filled."""
    # Arrange
    calendar = Calendar(user_id=1, name="Test Calendar", url="http://example.com/test.ics")
    session.add(calendar)
    await session.flush()

    event_data = EventCreateSchema(
        user_id=1,
        title="Maximal Event",
        date_start=datetime.now(UTC),
        date_end=datetime.now(UTC) + timedelta(hours=2),
        reminder_offset=30 * 60,
        need_to_remind=True,
        description="A very detailed description of the event",
        rrule="FREQ=DAILY;INTERVAL=1",
        calendar_id=calendar.id,
    )

    # Act
    event = await repository.create(event_data)

    # Assert
    assert event.id is not None
    assert event.title == "Maximal Event"
    assert event.description == "A very detailed description of the event"
    assert event.rrule == "FREQ=DAILY;INTERVAL=1"
    assert event.calendar_id == calendar.id


@pytest.mark.asyncio
async def test_create_event_with_same_start_end_date(
    repository: "EventRepository", test_user_settings: "Settings"
) -> None:
    """Test event creation with date_start == date_end (instant event)."""
    # Arrange
    now = datetime.now(UTC)
    event_data = EventCreateSchema(
        user_id=1,
        title="Instant Event",
        date_start=now,
        date_end=now,  # Same as start
        reminder_offset=15 * 60,
        need_to_remind=True,
        description=None,
        rrule=None,
        calendar_id=None,
    )

    # Act
    event = await repository.create(event_data)

    # Assert
    assert event.date_start == event.date_end


@pytest.mark.asyncio
async def test_create_event_creates_reminder_when_need_to_remind_true(
    repository: "EventRepository", session: "AsyncSession", test_user_settings: "Settings"
) -> None:
    """Test that creating an event with need_to_remind=True creates a Reminder."""
    # Arrange
    now = datetime.now(UTC)
    reminder_offset = 15 * 60  # 15 minutes
    event_data = EventCreateSchema(
        user_id=1,
        title="Event With Reminder",
        date_start=now + timedelta(hours=1),
        date_end=now + timedelta(hours=2),
        reminder_offset=reminder_offset,
        need_to_remind=True,
        description=None,
        rrule=None,
        calendar_id=None,
    )

    # Act
    event = await repository.create(event_data)

    # Assert
    stmt = select(Reminder).where(Reminder.event_id == event.id)
    result = await session.execute(stmt)
    reminder = result.scalar_one_or_none()

    assert reminder is not None
    assert reminder.event_id == event.id
    assert reminder.user_id == event.user_id
    assert reminder.sent is False
    # Check that remind_at is correctly calculated: date_start - reminder_offset
    expected_remind_at = event.date_start - timedelta(seconds=reminder_offset)
    assert reminder.remind_at == expected_remind_at


@pytest.mark.asyncio
async def test_create_event_does_not_create_reminder_when_need_to_remind_false(
    repository: "EventRepository", session: "AsyncSession", test_user_settings: "Settings"
) -> None:
    """Test that creating an event with need_to_remind=False does not create a Reminder."""
    # Arrange
    now = datetime.now(UTC)
    event_data = EventCreateSchema(
        user_id=1,
        title="Event Without Reminder",
        date_start=now + timedelta(hours=1),
        date_end=now + timedelta(hours=2),
        reminder_offset=15 * 60,
        need_to_remind=False,
        description=None,
        rrule=None,
        calendar_id=None,
    )

    # Act
    event = await repository.create(event_data)

    # Assert
    stmt = select(Reminder).where(Reminder.event_id == event.id)
    result = await session.execute(stmt)
    reminder = result.scalar_one_or_none()

    assert reminder is None


@pytest.mark.asyncio
async def test_create_event_reminder_uses_default_offset(
    repository: "EventRepository", session: "AsyncSession", test_user_settings: "Settings"
) -> None:
    """Test that reminder is created with correct remind_at when using default reminder_offset."""
    # Arrange
    now = datetime.now(UTC)
    event_data = EventCreateSchema(
        user_id=1,
        title="Event With Default Offset",
        date_start=now + timedelta(hours=1),
        date_end=now + timedelta(hours=2),
        reminder_offset=None,  # Will use default from settings
        need_to_remind=True,
        description=None,
        rrule=None,
        calendar_id=None,
    )

    # Act
    event = await repository.create(event_data)

    # Assert
    stmt = select(Reminder).where(Reminder.event_id == event.id)
    result = await session.execute(stmt)
    reminder = result.scalar_one_or_none()

    assert reminder is not None
    # Check that remind_at uses the default reminder_offset from settings
    expected_remind_at = event.date_start - timedelta(seconds=test_user_settings.default_reminder_offset)
    assert reminder.remind_at == expected_remind_at


@pytest.mark.asyncio
async def test_update_all_fields(
    repository: "EventRepository", session: "AsyncSession", test_user_settings: "Settings"
) -> None:
    """Test updating all fields of an event."""
    # Arrange
    calendar = Calendar(user_id=1, name="Work", url="http://example.com/work.ics")
    session.add(calendar)
    await session.flush()

    event = Event(
        user_id=1,
        title="Original Title",
        description="Original Description",
        date_start=datetime.now(UTC),
        date_end=datetime.now(UTC) + timedelta(hours=1),
        reminder_offset=15 * 60,
        need_to_remind=True,
        rrule=None,
        calendar_id=None,
    )
    session.add(event)
    await session.flush()
    event_id = event.id

    new_date_start = datetime.now(UTC) + timedelta(days=1)
    new_date_end = datetime.now(UTC) + timedelta(days=1, hours=2)
    update_data = EventUpdateSchema(
        title="New Title",
        description="New Description",
        date_start=new_date_start,
        date_end=new_date_end,
        reminder_offset=30 * 60,
        need_to_remind=False,
        rrule="FREQ=WEEKLY",
        calendar_id=calendar.id,
    )

    # Act
    updated = await repository.update(event_id, update_data)

    # Assert
    assert updated.title == "New Title"
    assert updated.description == "New Description"
    # Compare datetime objects, handling timezone differences
    assert updated.date_start.replace(tzinfo=None) == new_date_start.replace(tzinfo=None)
    assert updated.date_end.replace(tzinfo=None) == new_date_end.replace(tzinfo=None)
    assert updated.reminder_offset == 30 * 60
    assert updated.need_to_remind is False
    assert updated.rrule == "FREQ=WEEKLY"
    assert updated.calendar_id == calendar.id


@pytest.mark.asyncio
async def test_update_with_none_values(
    repository: "EventRepository", session: "AsyncSession", test_user_settings: "Settings"
) -> None:
    """Test that updating with None values doesn't clear fields (None means don't update)."""
    # Arrange
    event = Event(
        user_id=1,
        title="Test Event",
        description="Some Description",
        date_start=datetime.now(UTC),
        date_end=datetime.now(UTC) + timedelta(hours=1),
        reminder_offset=15 * 60,
        need_to_remind=True,
        rrule="FREQ=DAILY",
        calendar_id=None,
    )
    session.add(event)
    await session.flush()
    event_id = event.id

    # Update with no fields set (empty schema) - should not change anything
    # Pydantic's exclude_unset=True means None values are excluded if not explicitly set
    update_data = EventUpdateSchema()  # Empty update - no fields set  # type: ignore[call-arg]

    # Act
    updated = await repository.update(event_id, update_data)

    # Assert
    assert updated.title == "Test Event"  # Unchanged
    assert updated.description == "Some Description"  # Unchanged
    assert updated.rrule == "FREQ=DAILY"  # Unchanged


@pytest.mark.asyncio
async def test_find_with_no_filters(
    repository: "EventRepository", session: "AsyncSession", test_user_settings: "Settings"
) -> None:
    """Test find() method with no filters (should return all events)."""
    # Arrange
    event1 = Event(
        user_id=1,
        title="Event 1",
        date_start=datetime.now(UTC),
        date_end=datetime.now(UTC) + timedelta(hours=1),
        reminder_offset=15 * 60,
    )
    event2 = Event(
        user_id=2,
        title="Event 2",
        date_start=datetime.now(UTC),
        date_end=datetime.now(UTC) + timedelta(hours=1),
        reminder_offset=15 * 60,
    )
    session.add_all([event1, event2])
    await session.flush()

    filter = EventFilter(
        user_id=None,
        calendar_id=None,
        start_date_from=None,
        start_date_to=None,
        need_to_remind=None,
        limit=100,
        offset=0,
    )  # No filters

    # Act
    events = await repository.find(filter)

    # Assert
    assert len(events) == 2


@pytest.mark.asyncio
async def test_find_with_pagination_offset_exceeds_total(
    repository: "EventRepository", session: "AsyncSession", test_user_settings: "Settings"
) -> None:
    """Test find() with offset greater than total number of events."""
    # Arrange
    event = Event(
        user_id=1,
        title="Single Event",
        date_start=datetime.now(UTC),
        date_end=datetime.now(UTC) + timedelta(hours=1),
        reminder_offset=15 * 60,
    )
    session.add(event)
    await session.flush()

    filter = EventFilter(
        user_id=1,
        limit=10,
        offset=100,  # Offset exceeds total
        calendar_id=None,
        start_date_from=None,
        start_date_to=None,
        need_to_remind=None,
    )

    # Act
    events = await repository.find(filter)

    # Assert
    assert events == []


@pytest.mark.asyncio
async def test_find_with_zero_limit(
    repository: "EventRepository", session: "AsyncSession", test_user_settings: "Settings"
) -> None:
    """Test find() with limit=1 (minimum valid limit, EventFilter doesn't allow limit=0)."""
    # Arrange
    event = Event(
        user_id=1,
        title="Test Event",
        date_start=datetime.now(UTC),
        date_end=datetime.now(UTC) + timedelta(hours=1),
        reminder_offset=15 * 60,
    )
    session.add(event)
    await session.flush()

    # EventFilter has ge=1 validation, so limit=0 is not allowed
    # Test with minimum limit instead
    filter = EventFilter(
        user_id=1,
        limit=1,
        calendar_id=None,
        start_date_from=None,
        start_date_to=None,
        need_to_remind=None,
        offset=0,
    )

    # Act
    events = await repository.find(filter)

    # Assert
    assert len(events) == 1


@pytest.mark.asyncio
async def test_delete_event_success_with_user_id_check(
    repository: "EventRepository", session: "AsyncSession", test_user_settings: "Settings"
) -> None:
    """Test successful deletion when user_id matches."""
    # Arrange
    event = Event(
        user_id=1,
        title="Event to Delete",
        date_start=datetime.now(UTC),
        date_end=datetime.now(UTC) + timedelta(hours=1),
        reminder_offset=15 * 60,
    )
    session.add(event)
    await session.flush()
    event_id = event.id

    # Act
    await repository.delete(event_id, user_id=1)  # Correct user

    # Assert
    from sqlalchemy import select

    result = await session.execute(select(Event).where(Event.id == event_id))
    assert result.scalar() is None


@pytest.mark.asyncio
async def test_find_with_need_to_remind_filter(
    repository: "EventRepository", session: "AsyncSession", test_user_settings: "Settings"
) -> None:
    """Test find() with need_to_remind filter."""
    # Arrange
    event1 = Event(
        user_id=1,
        title="With Reminder",
        date_start=datetime.now(UTC),
        date_end=datetime.now(UTC) + timedelta(hours=1),
        reminder_offset=15 * 60,
        need_to_remind=True,
    )
    event2 = Event(
        user_id=1,
        title="Without Reminder",
        date_start=datetime.now(UTC),
        date_end=datetime.now(UTC) + timedelta(hours=1),
        reminder_offset=15 * 60,
        need_to_remind=False,
    )
    session.add_all([event1, event2])
    await session.flush()

    filter = EventFilter(
        user_id=1,
        need_to_remind=True,
        calendar_id=None,
        start_date_from=None,
        start_date_to=None,
        limit=100,
        offset=0,
    )

    # Act
    events = await repository.find(filter)

    # Assert
    assert len(events) == 1
    assert events[0].need_to_remind is True

    # Arrange for second test
    filter = EventFilter(
        user_id=1,
        need_to_remind=False,
        calendar_id=None,
        start_date_from=None,
        start_date_to=None,
        limit=100,
        offset=0,
    )

    # Act
    events = await repository.find(filter)

    # Assert
    assert len(events) == 1
    assert events[0].need_to_remind is False
