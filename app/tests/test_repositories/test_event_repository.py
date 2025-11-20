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
from sqlalchemy import text

from database.database import Base, get_engine, get_session_maker
from models.calendar import Calendar
from models.event import Event
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
async def test_create_event_success(repository: "EventRepository", test_user_settings) -> None:
    """Test successful event creation."""
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
    event = await repository.create(event_data)
    assert event.id is not None
    assert event.title == "Test Event"
    assert event.user_id == 1


@pytest.mark.asyncio
async def test_create_event_with_default_reminder_offset(
    repository: "EventRepository", test_user_settings: "Settings"
) -> None:
    """Test event creation with default reminder offset from settings."""
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
    event = await repository.create(event_data)
    assert event.reminder_offset == test_user_settings.default_reminder_offset


@pytest.mark.asyncio
async def test_create_event_with_calendar_id(
    repository: "EventRepository", session: "AsyncSession", test_user_settings: "Settings"
) -> None:
    """Test event creation with calendar_id."""
    # First create a calendar
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
    event = await repository.create(event_data)
    assert event.calendar_id == calendar.id


# ============================================================================
# READ OPERATIONS
# ============================================================================


@pytest.mark.asyncio
async def test_get_by_id_success(
    repository: "EventRepository", session: "AsyncSession", test_user_settings: "Settings"
) -> None:
    """Test retrieving event by ID."""
    # Create event directly first
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

    retrieved = await repository.get_by_id(event_id)
    assert retrieved is not None
    assert retrieved.id == event_id
    assert retrieved.title == "Test Event"


@pytest.mark.asyncio
async def test_get_by_id_not_found(repository: "EventRepository") -> None:
    """Test retrieving non-existent event by ID."""
    result = await repository.get_by_id(999)
    assert result is None


@pytest.mark.asyncio
async def test_get_by_user_id(
    repository: "EventRepository", session: "AsyncSession", test_user_settings: "Settings"
) -> None:
    """Test retrieving all events for a user."""
    # Create multiple events for user 1
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

    events = await repository.get_by_user_id(1)
    assert len(events) == 2
    assert all(e.user_id == 1 for e in events)


@pytest.mark.asyncio
async def test_get_by_user_id_empty(repository: "EventRepository") -> None:
    """Test retrieving events for user with no events."""
    events = await repository.get_by_user_id(1)
    assert events == []


@pytest.mark.asyncio
async def test_get_by_date_range(
    repository: "EventRepository", session: "AsyncSession", test_user_settings: "Settings"
) -> None:
    """Test retrieving events within a date range using EventFilter."""
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
    events = await repository.find(filter)
    assert len(events) == 1
    assert events[0].title == "Current Event"


@pytest.mark.asyncio
async def test_get_upcoming_events(
    repository: "EventRepository", session: "AsyncSession", test_user_settings: "Settings"
) -> None:
    """Test retrieving upcoming events for reminders."""
    now = datetime.now(UTC)
    past_event = Event(
        user_id=1,
        title="Past Event",
        date_start=now - timedelta(hours=1),
        date_end=now,
        reminder_offset=15 * 60,
        need_to_remind=True,
    )
    upcoming_event = Event(
        user_id=1,
        title="Upcoming Event",
        date_start=now + timedelta(hours=1),
        date_end=now + timedelta(hours=2),
        reminder_offset=15 * 60,
        need_to_remind=True,
    )
    no_reminder_event = Event(
        user_id=1,
        title="No Reminder Event",
        date_start=now + timedelta(hours=1),
        date_end=now + timedelta(hours=2),
        reminder_offset=15 * 60,
        need_to_remind=False,
    )
    session.add_all([past_event, upcoming_event, no_reminder_event])
    await session.flush()

    events = await repository.get_upcoming_for_reminders(user_id=1, limit=10)
    assert len(events) == 1
    assert events[0].title == "Upcoming Event"
    assert events[0].need_to_remind is True


# ============================================================================
# UPDATE OPERATIONS
# ============================================================================


@pytest.mark.asyncio
async def test_update_event_success(
    repository: "EventRepository", session: "AsyncSession", test_user_settings: "Settings"
) -> None:
    """Test successful event update."""
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
    updated = await repository.update(event_id, update_data)
    assert updated.title == "Updated Title"
    assert updated.description == "New description"
    assert updated.id == event_id


@pytest.mark.asyncio
async def test_update_event_not_found(repository: "EventRepository") -> None:
    """Test updating non-existent event."""
    update_data = EventUpdateSchema(title="New Title")  # type: ignore[call-arg]
    with pytest.raises(EventNotFoundError):
        await repository.update(999, update_data)


@pytest.mark.asyncio
async def test_update_event_partial(
    repository: "EventRepository", session: "AsyncSession", test_user_settings: "Settings"
) -> None:
    """Test partial event update (only some fields)."""
    event = Event(
        user_id=1,
        title="Original Title",
        description="Original Description",
        date_start=datetime.now(UTC),
        date_end=datetime.now(UTC) + timedelta(hours=1),
        reminder_offset=15 * 60,
    )
    session.add(event)
    await session.flush()
    event_id = event.id

    update_data = EventUpdateSchema(title="Updated Title")  # type: ignore[call-arg]
    updated = await repository.update(event_id, update_data)
    assert updated.title == "Updated Title"
    assert updated.description == "Original Description"  # Unchanged


# ============================================================================
# DELETE OPERATIONS
# ============================================================================


@pytest.mark.asyncio
async def test_delete_event_success(
    repository: "EventRepository", session: "AsyncSession", test_user_settings: "Settings"
) -> None:
    """Test successful event deletion."""
    from sqlalchemy import select

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

    await repository.delete(event_id)

    # Verify deletion
    result = await session.execute(select(Event).where(Event.id == event_id))
    assert result.scalar() is None


@pytest.mark.asyncio
async def test_delete_event_not_found(repository: "EventRepository") -> None:
    """Test deleting non-existent event."""
    with pytest.raises(EventNotFoundError):
        await repository.delete(999)


@pytest.mark.asyncio
async def test_delete_event_checks_user_ownership(
    repository: "EventRepository", session: "AsyncSession", test_user_settings: "Settings"
) -> None:
    """Test that deletion checks user ownership."""
    event = Event(
        user_id=1,
        title="User 1 Event",
        date_start=datetime.now(UTC),
        date_end=datetime.now(UTC) + timedelta(hours=1),
        reminder_offset=15 * 60,
    )
    session.add(event)
    await session.flush()
    event_id = event.id

    # Try to delete event belonging to different user
    with pytest.raises(EventNotFoundError):
        await repository.delete(event_id, user_id=2)  # Different user


# ============================================================================
# EDGE CASES AND VALIDATION
# ============================================================================


@pytest.mark.asyncio
async def test_get_by_date_range_inclusive_boundaries(
    repository: "EventRepository", session: "AsyncSession", test_user_settings: "Settings"
) -> None:
    """Test that date range boundaries are inclusive using EventFilter."""
    now = datetime.now(UTC)
    event_at_start = Event(
        user_id=1,
        title="Event at Start",
        date_start=now,
        date_end=now + timedelta(hours=1),
        reminder_offset=15 * 60,
    )
    event_at_end = Event(
        user_id=1,
        title="Event at End",
        date_start=now + timedelta(days=1),
        date_end=now + timedelta(days=1, hours=1),
        reminder_offset=15 * 60,
    )
    session.add_all([event_at_start, event_at_end])
    await session.flush()

    filter = EventFilter(
        user_id=1,
        start_date_from=now,
        start_date_to=now + timedelta(days=1),
        calendar_id=None,
        need_to_remind=None,
        limit=100,
        offset=0,
    )
    events = await repository.find(filter)
    assert len(events) == 2


@pytest.mark.asyncio
async def test_get_upcoming_events_respects_need_to_remind(
    repository: "EventRepository", session: "AsyncSession", test_user_settings: "Settings"
) -> None:
    """Test that get_upcoming_for_reminders only returns events with need_to_remind=True."""
    now = datetime.now(UTC)
    event_with_reminder = Event(
        user_id=1,
        title="With Reminder",
        date_start=now + timedelta(hours=1),
        date_end=now + timedelta(hours=2),
        reminder_offset=15 * 60,
        need_to_remind=True,
    )
    event_without_reminder = Event(
        user_id=1,
        title="Without Reminder",
        date_start=now + timedelta(hours=1),
        date_end=now + timedelta(hours=2),
        reminder_offset=15 * 60,
        need_to_remind=False,
    )
    session.add_all([event_with_reminder, event_without_reminder])
    await session.flush()

    events = await repository.get_upcoming_for_reminders(user_id=1, limit=10)
    assert len(events) == 1
    assert events[0].need_to_remind is True


# ============================================================================
# FILTER OPERATIONS (find method)
# ============================================================================


@pytest.mark.asyncio
async def test_find_with_multiple_filters(
    repository: "EventRepository", session: "AsyncSession", test_user_settings: "Settings"
) -> None:
    """Test find() method with multiple filters combined."""
    calendar = Calendar(user_id=1, name="Work", url="http://example.com/work.ics")
    session.add(calendar)
    await session.flush()

    event1 = Event(
        user_id=1,
        title="Work Event",
        date_start=datetime.now(UTC),
        date_end=datetime.now(UTC) + timedelta(hours=1),
        reminder_offset=15 * 60,
        calendar_id=calendar.id,
        need_to_remind=True,
    )
    event2 = Event(
        user_id=1,
        title="Personal Event",
        date_start=datetime.now(UTC),
        date_end=datetime.now(UTC) + timedelta(hours=1),
        reminder_offset=15 * 60,
        need_to_remind=True,
    )
    session.add_all([event1, event2])
    await session.flush()

    filter = EventFilter(
        user_id=1,
        calendar_id=calendar.id,
        need_to_remind=True,
        start_date_from=None,
        start_date_to=None,
        limit=100,
        offset=0,
    )
    events = await repository.find(filter)
    assert len(events) == 1
    assert events[0].title == "Work Event"


@pytest.mark.asyncio
async def test_find_with_pagination(
    repository: "EventRepository", session: "AsyncSession", test_user_settings: "Settings"
) -> None:
    """Test find() method with limit and offset."""
    events = [
        Event(
            user_id=1,
            title=f"Event {i}",
            date_start=datetime.now(UTC) + timedelta(minutes=i),  # Different times for ordering
            date_end=datetime.now(UTC) + timedelta(hours=1, minutes=i),
            reminder_offset=15 * 60,
        )
        for i in range(10)
    ]
    session.add_all(events)
    await session.flush()

    filter = EventFilter(
        user_id=1,
        limit=5,
        offset=0,
        calendar_id=None,
        start_date_from=None,
        start_date_to=None,
        need_to_remind=None,
    )
    first_page = await repository.find(filter)
    assert len(first_page) == 5

    filter = EventFilter(
        user_id=1,
        limit=5,
        offset=5,
        calendar_id=None,
        start_date_from=None,
        start_date_to=None,
        need_to_remind=None,
    )
    second_page = await repository.find(filter)
    assert len(second_page) == 5
    assert first_page[0].id != second_page[0].id


@pytest.mark.asyncio
async def test_find_empty_result(repository: "EventRepository") -> None:
    """Test find() method with filters that match no events."""
    filter = EventFilter(
        user_id=999,
        calendar_id=None,
        start_date_from=None,
        start_date_to=None,
        need_to_remind=None,
        limit=100,
        offset=0,
    )
    events = await repository.find(filter)
    assert events == []


# ============================================================================
# EDGE CASES AND BOUNDARY CONDITIONS
# ============================================================================


@pytest.mark.asyncio
async def test_create_event_without_settings_fallback(repository: "EventRepository", session: "AsyncSession") -> None:
    """Test event creation without user settings - should use fallback (15 minutes)."""
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
    event = await repository.create(event_data)
    assert event.reminder_offset == 15 * 60  # Fallback: 15 minutes


@pytest.mark.asyncio
async def test_create_event_with_minimal_data(repository: "EventRepository", test_user_settings: "Settings") -> None:
    """Test event creation with minimal required data."""
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
    event = await repository.create(event_data)
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
    event = await repository.create(event_data)
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
    event = await repository.create(event_data)
    assert event.date_start == event.date_end


@pytest.mark.asyncio
async def test_update_all_fields(
    repository: "EventRepository", session: "AsyncSession", test_user_settings: "Settings"
) -> None:
    """Test updating all fields of an event."""
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
    updated = await repository.update(event_id, update_data)
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
    updated = await repository.update(event_id, update_data)
    assert updated.title == "Test Event"  # Unchanged
    assert updated.description == "Some Description"  # Unchanged
    assert updated.rrule == "FREQ=DAILY"  # Unchanged


@pytest.mark.asyncio
async def test_find_with_no_filters(
    repository: "EventRepository", session: "AsyncSession", test_user_settings: "Settings"
) -> None:
    """Test find() method with no filters (should return all events)."""
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
    events = await repository.find(filter)
    assert len(events) == 2


@pytest.mark.asyncio
async def test_find_with_pagination_offset_exceeds_total(
    repository: "EventRepository", session: "AsyncSession", test_user_settings: "Settings"
) -> None:
    """Test find() with offset greater than total number of events."""
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
    events = await repository.find(filter)
    assert events == []


@pytest.mark.asyncio
async def test_find_with_zero_limit(
    repository: "EventRepository", session: "AsyncSession", test_user_settings: "Settings"
) -> None:
    """Test find() with limit=1 (minimum valid limit, EventFilter doesn't allow limit=0)."""
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
    events = await repository.find(filter)
    assert len(events) == 1


@pytest.mark.asyncio
async def test_get_upcoming_for_reminders_with_zero_limit(
    repository: "EventRepository", session: "AsyncSession", test_user_settings: "Settings"
) -> None:
    """Test get_upcoming_for_reminders() with limit=0 (should return empty list)."""
    now = datetime.now(UTC)
    event = Event(
        user_id=1,
        title="Upcoming Event",
        date_start=now + timedelta(hours=1),
        date_end=now + timedelta(hours=2),
        reminder_offset=15 * 60,
        need_to_remind=True,
    )
    session.add(event)
    await session.flush()

    # limit=0 is valid for get_upcoming_for_reminders (no validation in method signature)
    events = await repository.get_upcoming_for_reminders(user_id=1, limit=0)
    assert events == []


@pytest.mark.asyncio
async def test_get_upcoming_for_reminders_respects_limit(
    repository: "EventRepository", session: "AsyncSession", test_user_settings: "Settings"
) -> None:
    """Test that get_upcoming_for_reminders() respects the limit parameter."""
    now = datetime.now(UTC)
    events = [
        Event(
            user_id=1,
            title=f"Event {i}",
            date_start=now + timedelta(hours=i + 1),
            date_end=now + timedelta(hours=i + 2),
            reminder_offset=15 * 60,
            need_to_remind=True,
        )
        for i in range(10)
    ]
    session.add_all(events)
    await session.flush()

    result = await repository.get_upcoming_for_reminders(user_id=1, limit=5)
    assert len(result) == 5


@pytest.mark.asyncio
async def test_get_by_user_id_ordering(
    repository: "EventRepository", session: "AsyncSession", test_user_settings: "Settings"
) -> None:
    """Test that get_by_user_id() returns events ordered by date_start."""
    now = datetime.now(UTC)
    event1 = Event(
        user_id=1,
        title="Event 1",
        date_start=now + timedelta(days=2),
        date_end=now + timedelta(days=2, hours=1),
        reminder_offset=15 * 60,
    )
    event2 = Event(
        user_id=1,
        title="Event 2",
        date_start=now,
        date_end=now + timedelta(hours=1),
        reminder_offset=15 * 60,
    )
    event3 = Event(
        user_id=1,
        title="Event 3",
        date_start=now + timedelta(days=1),
        date_end=now + timedelta(days=1, hours=1),
        reminder_offset=15 * 60,
    )
    session.add_all([event1, event2, event3])
    await session.flush()

    events = await repository.get_by_user_id(1)
    assert len(events) == 3
    assert events[0].title == "Event 2"  # Earliest
    assert events[1].title == "Event 3"
    assert events[2].title == "Event 1"  # Latest


@pytest.mark.asyncio
async def test_delete_event_success_with_user_id_check(
    repository: "EventRepository", session: "AsyncSession", test_user_settings: "Settings"
) -> None:
    """Test successful deletion when user_id matches."""
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

    await repository.delete(event_id, user_id=1)  # Correct user

    from sqlalchemy import select

    result = await session.execute(select(Event).where(Event.id == event_id))
    assert result.scalar() is None


@pytest.mark.asyncio
async def test_find_with_need_to_remind_filter(
    repository: "EventRepository", session: "AsyncSession", test_user_settings: "Settings"
) -> None:
    """Test find() with need_to_remind filter."""
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
    events = await repository.find(filter)
    assert len(events) == 1
    assert events[0].need_to_remind is True

    filter = EventFilter(
        user_id=1,
        need_to_remind=False,
        calendar_id=None,
        start_date_from=None,
        start_date_to=None,
        limit=100,
        offset=0,
    )
    events = await repository.find(filter)
    assert len(events) == 1
    assert events[0].need_to_remind is False
