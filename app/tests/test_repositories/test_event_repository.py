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

from database.database import Base, get_engine, get_session_maker
from models.settings import Settings
from repositories.schemas import EventCreateSchema

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from repositories.event_repository import EventRepository


@pytest_asyncio.fixture
async def engine():
    """Create an async engine and ensure tables are created for tests."""
    engine = get_engine("sqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Enable foreign keys for SQLite
        await conn.run_sync(lambda sync_conn: sync_conn.execute(sync_conn.text("PRAGMA foreign_keys=ON;")))
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
async def test_create_event_success(
    repository: "EventRepository", test_user_settings: Settings
) -> None:
    """Test successful event creation."""
    event_data = EventCreateSchema(
        user_id=1,
        title="Test Event",
        date_start=datetime.now(UTC),
        date_end=datetime.now(UTC) + timedelta(hours=1),
        reminder_offset=15 * 60,
    )
    event = await repository.create(event_data)
    assert event.id is not None
    assert event.title == "Test Event"
    assert event.user_id == 1


@pytest.mark.asyncio
async def test_create_event_with_default_reminder_offset(
    repository: "EventRepository", test_user_settings: Settings
) -> None:
    """Test event creation with default reminder offset from settings."""
    # TODO: Implement EventRepository.create() with default_reminder_offset
    # event_data = EventCreateSchema(
    #     user_id=1,
    #     title="Test Event",
    #     date_start=datetime.now(UTC),
    #     date_end=datetime.now(UTC) + timedelta(hours=1),
    #     # reminder_offset not provided - should use default from settings
    # )
    # event = await repository.create(event_data)
    # assert event.reminder_offset == test_user_settings.default_reminder_offset
    pass


@pytest.mark.asyncio
async def test_create_event_with_calendar_id(
    repository: "EventRepository", session: "AsyncSession", test_user_settings: Settings
) -> None:
    """Test event creation with calendar_id."""
    # TODO: Implement EventRepository.create() with calendar_id
    # First create a calendar
    # calendar = Calendar(user_id=1, name="Work", url="http://example.com/work.ics")
    # session.add(calendar)
    # await session.flush()
    #
    # event_data = EventCreateSchema(
    #     user_id=1,
    #     title="Work Event",
    #     date_start=datetime.now(UTC),
    #     date_end=datetime.now(UTC) + timedelta(hours=1),
    #     calendar_id=calendar.id,
    # )
    # event = await repository.create(event_data)
    # assert event.calendar_id == calendar.id
    pass


# ============================================================================
# READ OPERATIONS
# ============================================================================


@pytest.mark.asyncio
async def test_get_by_id_success(
    repository: "EventRepository", session: "AsyncSession", test_user_settings: Settings
) -> None:
    """Test retrieving event by ID."""
    # TODO: Implement EventRepository.get_by_id()
    # Create event directly first
    # event = Event(
    #     user_id=1,
    #     title="Test Event",
    #     date_start=datetime.now(UTC),
    #     date_end=datetime.now(UTC) + timedelta(hours=1),
    #     reminder_offset=15 * 60,
    # )
    # session.add(event)
    # await session.flush()
    # event_id = event.id
    #
    # retrieved = await repository.get_by_id(event_id)
    # assert retrieved is not None
    # assert retrieved.id == event_id
    # assert retrieved.title == "Test Event"
    pass


@pytest.mark.asyncio
async def test_get_by_id_not_found(repository: "EventRepository") -> None:
    """Test retrieving non-existent event by ID."""
    # TODO: Implement EventRepository.get_by_id() with None return
    # result = await repository.get_by_id(999)
    # assert result is None
    pass


@pytest.mark.asyncio
async def test_get_by_user_id(
    repository: "EventRepository", session: "AsyncSession", test_user_settings: Settings
) -> None:
    """Test retrieving all events for a user."""
    # TODO: Implement EventRepository.get_by_user_id()
    # Create multiple events for user 1
    # event1 = Event(
    #     user_id=1,
    #     title="Event 1",
    #     date_start=datetime.now(UTC),
    #     date_end=datetime.now(UTC) + timedelta(hours=1),
    #     reminder_offset=15 * 60,
    # )
    # event2 = Event(
    #     user_id=1,
    #     title="Event 2",
    #     date_start=datetime.now(UTC),
    #     date_end=datetime.now(UTC) + timedelta(hours=1),
    #     reminder_offset=15 * 60,
    # )
    # event3 = Event(
    #     user_id=2,  # Different user
    #     title="Event 3",
    #     date_start=datetime.now(UTC),
    #     date_end=datetime.now(UTC) + timedelta(hours=1),
    #     reminder_offset=15 * 60,
    # )
    # session.add_all([event1, event2, event3])
    # await session.flush()
    #
    # events = await repository.get_by_user_id(1)
    # assert len(events) == 2
    # assert all(e.user_id == 1 for e in events)
    pass


@pytest.mark.asyncio
async def test_get_by_user_id_empty(repository: "EventRepository") -> None:
    """Test retrieving events for user with no events."""
    # TODO: Implement EventRepository.get_by_user_id() with empty list
    # events = await repository.get_by_user_id(1)
    # assert events == []
    pass


@pytest.mark.asyncio
async def test_get_by_date_range(
    repository: "EventRepository", session: "AsyncSession", test_user_settings: Settings
) -> None:
    """Test retrieving events within a date range using EventFilter."""
    # TODO: Implement EventRepository.find() with EventFilter
    # now = datetime.now(UTC)
    # past_event = Event(
    #     user_id=1,
    #     title="Past Event",
    #     date_start=now - timedelta(days=2),
    #     date_end=now - timedelta(days=2, hours=1),
    #     reminder_offset=15 * 60,
    # )
    # current_event = Event(
    #     user_id=1,
    #     title="Current Event",
    #     date_start=now,
    #     date_end=now + timedelta(hours=1),
    #     reminder_offset=15 * 60,
    # )
    # future_event = Event(
    #     user_id=1,
    #     title="Future Event",
    #     date_start=now + timedelta(days=2),
    #     date_end=now + timedelta(days=2, hours=1),
    #     reminder_offset=15 * 60,
    # )
    # session.add_all([past_event, current_event, future_event])
    # await session.flush()
    #
    # filter = EventFilter(
    #     user_id=1,
    #     start_date_from=now - timedelta(days=1),
    #     start_date_to=now + timedelta(days=1),
    # )
    # events = await repository.find(filter)
    # assert len(events) == 1
    # assert events[0].title == "Current Event"
    pass


@pytest.mark.asyncio
async def test_get_upcoming_events(
    repository: "EventRepository", session: "AsyncSession", test_user_settings: Settings
) -> None:
    """Test retrieving upcoming events for reminders."""
    # TODO: Implement EventRepository.get_upcoming_for_reminders()
    # now = datetime.now(UTC)
    # past_event = Event(
    #     user_id=1,
    #     title="Past Event",
    #     date_start=now - timedelta(hours=1),
    #     date_end=now,
    #     reminder_offset=15 * 60,
    #     need_to_remind=True,
    # )
    # upcoming_event = Event(
    #     user_id=1,
    #     title="Upcoming Event",
    #     date_start=now + timedelta(hours=1),
    #     date_end=now + timedelta(hours=2),
    #     reminder_offset=15 * 60,
    #     need_to_remind=True,
    # )
    # no_reminder_event = Event(
    #     user_id=1,
    #     title="No Reminder Event",
    #     date_start=now + timedelta(hours=1),
    #     date_end=now + timedelta(hours=2),
    #     reminder_offset=15 * 60,
    #     need_to_remind=False,
    # )
    # session.add_all([past_event, upcoming_event, no_reminder_event])
    # await session.flush()
    #
    # events = await repository.get_upcoming_for_reminders(user_id=1, limit=10)
    # assert len(events) == 1
    # assert events[0].title == "Upcoming Event"
    # assert events[0].need_to_remind is True
    pass


# ============================================================================
# UPDATE OPERATIONS
# ============================================================================


@pytest.mark.asyncio
async def test_update_event_success(
    repository: "EventRepository", session: "AsyncSession", test_user_settings: Settings
) -> None:
    """Test successful event update."""
    # TODO: Implement EventRepository.update()
    # event = Event(
    #     user_id=1,
    #     title="Original Title",
    #     date_start=datetime.now(UTC),
    #     date_end=datetime.now(UTC) + timedelta(hours=1),
    #     reminder_offset=15 * 60,
    # )
    # session.add(event)
    # await session.flush()
    # event_id = event.id
    #
    # update_data = EventUpdateSchema(title="Updated Title", description="New description")
    # updated = await repository.update(event_id, update_data)
    # assert updated.title == "Updated Title"
    # assert updated.description == "New description"
    # assert updated.id == event_id
    pass


@pytest.mark.asyncio
async def test_update_event_not_found(repository: "EventRepository") -> None:
    """Test updating non-existent event."""
    # TODO: Implement EventRepository.update() with exception
    # update_data = EventUpdateSchema(title="New Title")
    # with pytest.raises(EventNotFoundError):
    #     await repository.update(999, update_data)
    pass


@pytest.mark.asyncio
async def test_update_event_partial(
    repository: "EventRepository", session: "AsyncSession", test_user_settings: Settings
) -> None:
    """Test partial event update (only some fields)."""
    # TODO: Implement EventRepository.update() with partial update
    # event = Event(
    #     user_id=1,
    #     title="Original Title",
    #     description="Original Description",
    #     date_start=datetime.now(UTC),
    #     date_end=datetime.now(UTC) + timedelta(hours=1),
    #     reminder_offset=15 * 60,
    # )
    # session.add(event)
    # await session.flush()
    # event_id = event.id
    #
    # update_data = EventUpdateSchema(title="Updated Title")
    # updated = await repository.update(event_id, update_data)
    # assert updated.title == "Updated Title"
    # assert updated.description == "Original Description"  # Unchanged
    pass


# ============================================================================
# DELETE OPERATIONS
# ============================================================================


@pytest.mark.asyncio
async def test_delete_event_success(
    repository: "EventRepository", session: "AsyncSession", test_user_settings: Settings
) -> None:
    """Test successful event deletion."""
    # TODO: Implement EventRepository.delete()
    # event = Event(
    #     user_id=1,
    #     title="Event to Delete",
    #     date_start=datetime.now(UTC),
    #     date_end=datetime.now(UTC) + timedelta(hours=1),
    #     reminder_offset=15 * 60,
    # )
    # session.add(event)
    # await session.flush()
    # event_id = event.id
    #
    # await repository.delete(event_id)
    #
    # # Verify deletion
    # result = await session.execute(select(Event).where(Event.id == event_id))
    # assert result.scalar() is None
    pass


@pytest.mark.asyncio
async def test_delete_event_not_found(repository: "EventRepository") -> None:
    """Test deleting non-existent event."""
    # TODO: Implement EventRepository.delete() with exception
    # with pytest.raises(EventNotFoundError):
    #     await repository.delete(999)
    pass


@pytest.mark.asyncio
async def test_delete_event_checks_user_ownership(
    repository: "EventRepository", session: "AsyncSession", test_user_settings: Settings
) -> None:
    """Test that deletion checks user ownership."""
    # TODO: Implement EventRepository.delete() with ownership check
    # event = Event(
    #     user_id=1,
    #     title="User 1 Event",
    #     date_start=datetime.now(UTC),
    #     date_end=datetime.now(UTC) + timedelta(hours=1),
    #     reminder_offset=15 * 60,
    # )
    # session.add(event)
    # await session.flush()
    # event_id = event.id
    #
    # # Try to delete event belonging to different user
    # with pytest.raises(EventNotFoundError):
    #     await repository.delete(event_id, user_id=2)  # Different user
    pass


# ============================================================================
# EDGE CASES AND VALIDATION
# ============================================================================


@pytest.mark.asyncio
async def test_get_by_date_range_inclusive_boundaries(
    repository: "EventRepository", session: "AsyncSession", test_user_settings: Settings
) -> None:
    """Test that date range boundaries are inclusive using EventFilter."""
    # TODO: Implement EventRepository.find() with inclusive boundaries
    # now = datetime.now(UTC)
    # event_at_start = Event(
    #     user_id=1,
    #     title="Event at Start",
    #     date_start=now,
    #     date_end=now + timedelta(hours=1),
    #     reminder_offset=15 * 60,
    # )
    # event_at_end = Event(
    #     user_id=1,
    #     title="Event at End",
    #     date_start=now + timedelta(days=1),
    #     date_end=now + timedelta(days=1, hours=1),
    #     reminder_offset=15 * 60,
    # )
    # session.add_all([event_at_start, event_at_end])
    # await session.flush()
    #
    # filter = EventFilter(
    #     user_id=1,
    #     start_date_from=now,
    #     start_date_to=now + timedelta(days=1),
    # )
    # events = await repository.find(filter)
    # assert len(events) == 2
    pass


@pytest.mark.asyncio
async def test_get_upcoming_events_respects_need_to_remind(
    repository: "EventRepository", session: "AsyncSession", test_user_settings: Settings
) -> None:
    """Test that get_upcoming_for_reminders only returns events with need_to_remind=True."""
    # TODO: Implement EventRepository.get_upcoming_for_reminders() filtering
    # now = datetime.now(UTC)
    # event_with_reminder = Event(
    #     user_id=1,
    #     title="With Reminder",
    #     date_start=now + timedelta(hours=1),
    #     date_end=now + timedelta(hours=2),
    #     reminder_offset=15 * 60,
    #     need_to_remind=True,
    # )
    # event_without_reminder = Event(
    #     user_id=1,
    #     title="Without Reminder",
    #     date_start=now + timedelta(hours=1),
    #     date_end=now + timedelta(hours=2),
    #     reminder_offset=15 * 60,
    #     need_to_remind=False,
    # )
    # session.add_all([event_with_reminder, event_without_reminder])
    # await session.flush()
    #
    # events = await repository.get_upcoming_for_reminders(user_id=1, limit=10)
    # assert len(events) == 1
    # assert events[0].need_to_remind is True
    pass


# ============================================================================
# FILTER OPERATIONS (find method)
# ============================================================================


@pytest.mark.asyncio
async def test_find_with_multiple_filters(
    repository: "EventRepository", session: "AsyncSession", test_user_settings: Settings
) -> None:
    """Test find() method with multiple filters combined."""
    # TODO: Implement EventRepository.find() with multiple filters
    # calendar = Calendar(user_id=1, name="Work", url="http://example.com/work.ics")
    # session.add(calendar)
    # await session.flush()
    #
    # event1 = Event(
    #     user_id=1,
    #     title="Work Event",
    #     date_start=datetime.now(UTC),
    #     date_end=datetime.now(UTC) + timedelta(hours=1),
    #     reminder_offset=15 * 60,
    #     calendar_id=calendar.id,
    #     need_to_remind=True,
    # )
    # event2 = Event(
    #     user_id=1,
    #     title="Personal Event",
    #     date_start=datetime.now(UTC),
    #     date_end=datetime.now(UTC) + timedelta(hours=1),
    #     reminder_offset=15 * 60,
    #     need_to_remind=True,
    # )
    # session.add_all([event1, event2])
    # await session.flush()
    #
    # filter = EventFilter(user_id=1, calendar_id=calendar.id, need_to_remind=True)
    # events = await repository.find(filter)
    # assert len(events) == 1
    # assert events[0].title == "Work Event"
    pass


@pytest.mark.asyncio
async def test_find_with_pagination(
    repository: "EventRepository", session: "AsyncSession", test_user_settings: Settings
) -> None:
    """Test find() method with limit and offset."""
    # TODO: Implement EventRepository.find() with pagination
    # events = [
    #     Event(
    #         user_id=1,
    #         title=f"Event {i}",
    #         date_start=datetime.now(UTC),
    #         date_end=datetime.now(UTC) + timedelta(hours=1),
    #         reminder_offset=15 * 60,
    #     )
    #     for i in range(10)
    # ]
    # session.add_all(events)
    # await session.flush()
    #
    # filter = EventFilter(user_id=1, limit=5, offset=0)
    # first_page = await repository.find(filter)
    # assert len(first_page) == 5
    #
    # filter.offset = 5
    # second_page = await repository.find(filter)
    # assert len(second_page) == 5
    # assert first_page[0].id != second_page[0].id
    pass


@pytest.mark.asyncio
async def test_find_empty_result(repository: "EventRepository") -> None:
    """Test find() method with filters that match no events."""
    # TODO: Implement EventRepository.find() with empty result
    # filter = EventFilter(user_id=999)
    # events = await repository.find(filter)
    # assert events == []
    pass

