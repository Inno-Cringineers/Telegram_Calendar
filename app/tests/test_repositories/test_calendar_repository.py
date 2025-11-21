"""
Unit tests for CalendarRepository using TDD approach.

Tests cover:
- Creating calendars
- Retrieving calendars by ID
- Retrieving calendars by user_id
- Updating calendars
- Deleting calendars
- Filtering calendars with CalendarFilter
"""

from typing import TYPE_CHECKING

import pytest
import pytest_asyncio
from sqlalchemy import select, text

from database.database import Base, get_engine, get_session_maker
from models.calendar import Calendar
from repositories.exceptions import CalendarNotFoundError
from repositories.schemas import CalendarCreateSchema, CalendarFilter, CalendarUpdateSchema

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from repositories.calendar_repository import CalendarRepository  # noqa: F401, PLC0415


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
async def repository(session: "AsyncSession") -> "CalendarRepository":
    """Create CalendarRepository instance for tests.

    Note: Repository receives session directly, not through Store.
    This is the recommended approach - simple and explicit.
    """
    from repositories.calendar_repository import CalendarRepository  # noqa: PLC0415

    return CalendarRepository(session)


# ============================================================================
# CREATE OPERATIONS
# ============================================================================


@pytest.mark.asyncio
async def test_create_calendar_success(repository: "CalendarRepository") -> None:
    """Test successful calendar creation."""
    calendar_data = CalendarCreateSchema(
        user_id=1,
        name="Work Calendar",
        url="http://example.com/work.ics",
    )
    calendar = await repository.create(calendar_data)
    assert calendar.id is not None
    assert calendar.name == "Work Calendar"
    assert calendar.user_id == 1
    assert calendar.url == "http://example.com/work.ics"
    assert calendar.sync_enabled is True  # Default value
    assert calendar.last_sync is None  # Default value


@pytest.mark.asyncio
async def test_create_calendar_with_minimal_data(repository: "CalendarRepository") -> None:
    """Test calendar creation with minimal required data."""
    calendar_data = CalendarCreateSchema(
        user_id=1,
        name="Personal",
        url="https://example.com/personal.ics",
    )
    calendar = await repository.create(calendar_data)
    assert calendar.id is not None
    assert calendar.name == "Personal"
    assert calendar.url == "https://example.com/personal.ics"
    assert calendar.sync_enabled is True


@pytest.mark.asyncio
async def test_create_calendar_with_https_url(repository: "CalendarRepository") -> None:
    """Test calendar creation with HTTPS URL."""
    calendar_data = CalendarCreateSchema(
        user_id=1,
        name="Secure Calendar",
        url="https://example.com/secure.ics",
    )
    calendar = await repository.create(calendar_data)
    assert calendar.url == "https://example.com/secure.ics"


# ============================================================================
# READ OPERATIONS
# ============================================================================


@pytest.mark.asyncio
async def test_get_by_id_success(repository: "CalendarRepository", session: "AsyncSession") -> None:
    """Test retrieving calendar by ID."""
    # Create calendar directly first
    calendar = Calendar(
        user_id=1,
        name="Test Calendar",
        url="http://example.com/test.ics",
    )
    session.add(calendar)
    await session.flush()
    calendar_id = calendar.id

    retrieved = await repository.get_by_id(calendar_id)
    assert retrieved is not None
    assert retrieved.id == calendar_id
    assert retrieved.name == "Test Calendar"


@pytest.mark.asyncio
async def test_get_by_id_not_found(repository: "CalendarRepository") -> None:
    """Test retrieving non-existent calendar by ID."""
    result = await repository.get_by_id(999)
    assert result is None


@pytest.mark.asyncio
async def test_get_by_user_id(repository: "CalendarRepository", session: "AsyncSession") -> None:
    """Test retrieving all calendars for a user."""
    # Create multiple calendars for user 1
    calendar1 = Calendar(
        user_id=1,
        name="Work",
        url="http://example.com/work.ics",
    )
    calendar2 = Calendar(
        user_id=1,
        name="Personal",
        url="http://example.com/personal.ics",
    )
    calendar3 = Calendar(
        user_id=2,  # Different user
        name="Other User Calendar",
        url="http://example.com/other.ics",
    )
    session.add_all([calendar1, calendar2, calendar3])
    await session.flush()

    calendars = await repository.get_by_user_id(1)
    assert len(calendars) == 2
    assert all(c.user_id == 1 for c in calendars)
    assert {c.name for c in calendars} == {"Work", "Personal"}


@pytest.mark.asyncio
async def test_get_by_user_id_empty(repository: "CalendarRepository") -> None:
    """Test retrieving calendars for user with no calendars."""
    calendars = await repository.get_by_user_id(1)
    assert calendars == []


# ============================================================================
# UPDATE OPERATIONS
# ============================================================================


@pytest.mark.asyncio
async def test_update_calendar_success(repository: "CalendarRepository", session: "AsyncSession") -> None:
    """Test successful calendar update."""
    calendar = Calendar(
        user_id=1,
        name="Original Name",
        url="http://example.com/original.ics",
    )
    session.add(calendar)
    await session.flush()
    calendar_id = calendar.id

    update_data = CalendarUpdateSchema(name="Updated Name", url="http://example.com/updated.ics")  # type: ignore[call-arg]
    updated = await repository.update(calendar_id, update_data)
    assert updated.name == "Updated Name"
    assert updated.url == "http://example.com/updated.ics"
    assert updated.id == calendar_id


@pytest.mark.asyncio
async def test_update_calendar_not_found(repository: "CalendarRepository") -> None:
    """Test updating non-existent calendar."""
    update_data = CalendarUpdateSchema(name="New Name")  # type: ignore[call-arg]
    with pytest.raises(CalendarNotFoundError):
        await repository.update(999, update_data)


@pytest.mark.asyncio
async def test_update_calendar_partial(repository: "CalendarRepository", session: "AsyncSession") -> None:
    """Test partial calendar update (only some fields)."""
    calendar_data = CalendarCreateSchema(
        user_id=1,
        name="Original Name",
        url="http://example.com/original.ics",
    )
    calendar = await repository.create(calendar_data)

    update_data = CalendarUpdateSchema(name="Updated Name")  # type: ignore[call-arg]
    updated = await repository.update(calendar.id, update_data)
    assert updated.name == "Updated Name"
    assert updated.url == "http://example.com/original.ics"  # Unchanged


@pytest.mark.asyncio
async def test_update_calendar_url_only(repository: "CalendarRepository", session: "AsyncSession") -> None:
    """Test updating only URL field."""
    calendar_data = CalendarCreateSchema(
        user_id=1,
        name="Test Calendar",
        url="http://example.com/old.ics",
    )
    calendar = await repository.create(calendar_data)

    update_data = CalendarUpdateSchema(url="https://example.com/new.ics")  # type: ignore[call-arg]
    updated = await repository.update(calendar.id, update_data)
    assert updated.name == "Test Calendar"  # Unchanged
    assert updated.url == "https://example.com/new.ics"


@pytest.mark.asyncio
async def test_update_all_fields(repository: "CalendarRepository", session: "AsyncSession") -> None:
    """Test updating all fields of a calendar."""
    calendar = Calendar(
        user_id=1,
        name="Original Name",
        url="http://example.com/original.ics",
    )
    session.add(calendar)
    await session.flush()
    calendar_id = calendar.id

    update_data = CalendarUpdateSchema(
        name="New Name",
        url="https://example.com/new.ics",
    )
    updated = await repository.update(calendar_id, update_data)
    assert updated.name == "New Name"
    assert updated.url == "https://example.com/new.ics"


@pytest.mark.asyncio
async def test_update_with_none_values(repository: "CalendarRepository", session: "AsyncSession") -> None:
    """Test that updating with None values doesn't clear fields (None means don't update)."""
    calendar = Calendar(
        user_id=1,
        name="Test Calendar",
        url="http://example.com/test.ics",
    )
    session.add(calendar)
    await session.flush()
    calendar_id = calendar.id

    # Update with no fields set (empty schema) - should not change anything
    # Pydantic's exclude_unset=True means None values are excluded if not explicitly set
    update_data = CalendarUpdateSchema()  # Empty update - no fields set  # type: ignore[call-arg]
    updated = await repository.update(calendar_id, update_data)
    assert updated.name == "Test Calendar"  # Unchanged
    assert updated.url == "http://example.com/test.ics"  # Unchanged


# ============================================================================
# DELETE OPERATIONS
# ============================================================================


@pytest.mark.asyncio
async def test_delete_calendar_success(repository: "CalendarRepository") -> None:
    """Test successful calendar deletion."""
    calendar_data = CalendarCreateSchema(
        user_id=1,
        name="Calendar to Delete",
        url="http://example.com/delete.ics",
    )
    calendar = await repository.create(calendar_data)

    await repository.delete(calendar.id)

    # Verify deletion
    result = await repository.session.execute(select(Calendar).where(Calendar.id == calendar.id))
    assert result.scalar() is None


@pytest.mark.asyncio
async def test_delete_calendar_not_found(repository: "CalendarRepository") -> None:
    """Test deleting non-existent calendar."""
    with pytest.raises(CalendarNotFoundError):
        await repository.delete(999)


# ============================================================================
# FILTER OPERATIONS (find method)
# ============================================================================


@pytest.mark.asyncio
async def test_find_with_multiple_filters(repository: "CalendarRepository") -> None:
    """Test find() method with multiple filters combined."""
    calendar1_data = CalendarCreateSchema(
        user_id=1,
        name="Work",
        url="http://example.com/work.ics",
    )
    calendar2_data = CalendarCreateSchema(
        user_id=1,
        name="Personal",
        url="http://example.com/personal.ics",
    )
    calendar3_data = CalendarCreateSchema(
        user_id=2,
        name="Work2",
        url="http://example.com/work2.ics",
    )
    calendar1 = await repository.create(calendar1_data)
    await repository.create(calendar2_data)
    await repository.create(calendar3_data)

    filter = CalendarFilter(
        user_id=1,
        name="Work",
        url=None,
        limit=100,
        offset=0,
    )
    calendars = await repository.find(filter)
    assert len(calendars) == 1
    assert calendars[0].name == "Work"
    assert calendars[0].id == calendar1.id


@pytest.mark.asyncio
async def test_find_with_user_id_filter(repository: "CalendarRepository") -> None:
    """Test find() method with user_id filter."""
    calendar1_data = CalendarCreateSchema(
        user_id=1,
        name="User 1 Calendar",
        url="http://example.com/user1.ics",
    )
    calendar2_data = CalendarCreateSchema(
        user_id=2,
        name="User 2 Calendar",
        url="http://example.com/user2.ics",
    )
    await repository.create(calendar1_data)
    await repository.create(calendar2_data)

    filter = CalendarFilter(
        user_id=1,
        name=None,
        url=None,
        limit=100,
        offset=0,
    )
    calendars = await repository.find(filter)
    assert len(calendars) == 1
    assert calendars[0].user_id == 1


@pytest.mark.asyncio
async def test_find_with_name_filter(repository: "CalendarRepository") -> None:
    """Test find() method with name filter."""
    calendar1_data = CalendarCreateSchema(
        user_id=1,
        name="Work",
        url="http://example.com/work1.ics",
    )
    calendar2_data = CalendarCreateSchema(
        user_id=2,
        name="Work2",
        url="http://example.com/work2.ics",
    )
    await repository.create(calendar1_data)
    await repository.create(calendar2_data)

    filter = CalendarFilter(
        user_id=None,
        name="Work",
        url=None,
        limit=100,
        offset=0,
    )
    calendars = await repository.find(filter)
    assert len(calendars) == 1
    assert all(c.name == "Work" for c in calendars)


@pytest.mark.asyncio
async def test_find_with_url_filter(repository: "CalendarRepository") -> None:
    """Test find() method with url filter."""
    calendar_data = CalendarCreateSchema(
        user_id=1,
        name="Test Calendar",
        url="http://example.com/specific.ics",
    )
    await repository.create(calendar_data)

    filter = CalendarFilter(
        user_id=None,
        name=None,
        url="http://example.com/specific.ics",
        limit=100,
        offset=0,
    )
    calendars = await repository.find(filter)
    assert len(calendars) == 1
    assert calendars[0].url == "http://example.com/specific.ics"


@pytest.mark.asyncio
async def test_find_with_no_filters(repository: "CalendarRepository", session: "AsyncSession") -> None:
    """Test find() method with no filters (should return all calendars)."""
    calendar1 = Calendar(
        user_id=1,
        name="Calendar 1",
        url="http://example.com/cal1.ics",
    )
    calendar2 = Calendar(
        user_id=2,
        name="Calendar 2",
        url="http://example.com/cal2.ics",
    )
    session.add_all([calendar1, calendar2])
    await session.flush()

    filter = CalendarFilter(
        user_id=None,
        name=None,
        url=None,
        limit=100,
        offset=0,
    )
    calendars = await repository.find(filter)
    assert len(calendars) == 2


@pytest.mark.asyncio
async def test_find_empty_result(repository: "CalendarRepository") -> None:
    """Test find() method with filters that match no calendars."""
    filter = CalendarFilter(
        user_id=999,
        name=None,
        url=None,
        limit=100,
        offset=0,
    )
    calendars = await repository.find(filter)
    assert calendars == []


# ============================================================================
# EDGE CASES AND VALIDATION
# ============================================================================


@pytest.mark.asyncio
async def test_create_calendar_name_uniqueness(repository: "CalendarRepository", session: "AsyncSession") -> None:
    """Test that calendar name must be unique."""
    calendar1_data = CalendarCreateSchema(
        user_id=1,
        name="Unique Name",
        url="http://example.com/cal1.ics",
    )
    await repository.create(calendar1_data)

    # Try to create another calendar with the same name
    calendar2_data = CalendarCreateSchema(
        user_id=2,  # Different user, but name must still be unique
        name="Unique Name",
        url="http://example.com/cal2.ics",
    )
    await repository.session.flush()

    # This should raise an IntegrityError due to unique constraint
    from sqlalchemy.exc import IntegrityError

    with pytest.raises(IntegrityError):
        await repository.create(calendar2_data)
        await repository.session.flush()


@pytest.mark.asyncio
async def test_create_calendar_url_uniqueness(repository: "CalendarRepository", session: "AsyncSession") -> None:
    """Test that calendar URL must be unique."""
    calendar1_data = CalendarCreateSchema(
        user_id=1,
        name="Calendar 1",
        url="http://example.com/unique.ics",
    )
    await repository.create(calendar1_data)

    # Try to create another calendar with the same URL
    calendar2_data = CalendarCreateSchema(
        user_id=2,  # Different user, but URL must still be unique
        name="Calendar 2",
        url="http://example.com/unique.ics",
    )
    await repository.session.flush()

    # This should raise an IntegrityError due to unique constraint
    from sqlalchemy.exc import IntegrityError

    with pytest.raises(IntegrityError):
        await repository.create(calendar2_data)
        await repository.session.flush()


@pytest.mark.asyncio
async def test_calendar_sync_enabled_default(repository: "CalendarRepository") -> None:
    """Test that sync_enabled defaults to True."""
    calendar_data = CalendarCreateSchema(
        user_id=1,
        name="Test Calendar",
        url="http://example.com/test.ics",
    )
    calendar = await repository.create(calendar_data)
    assert calendar.sync_enabled is True


@pytest.mark.asyncio
async def test_calendar_last_sync_default(repository: "CalendarRepository") -> None:
    """Test that last_sync defaults to None."""
    calendar_data = CalendarCreateSchema(
        user_id=1,
        name="Test Calendar",
        url="http://example.com/test.ics",
    )
    calendar = await repository.create(calendar_data)
    assert calendar.last_sync is None


@pytest.mark.asyncio
async def test_find_with_combined_filters(repository: "CalendarRepository") -> None:
    """Test find() with multiple filters combined (user_id and name)."""
    calendar1_data = CalendarCreateSchema(
        user_id=1,
        name="Work",
        url="http://example.com/work1.ics",
    )
    calendar2_data = CalendarCreateSchema(
        user_id=1,
        name="Personal",
        url="http://example.com/personal.ics",
    )
    calendar3_data = CalendarCreateSchema(
        user_id=2,
        name="Work2",
        url="http://example.com/work2.ics",
    )
    calendar1 = await repository.create(calendar1_data)
    await repository.create(calendar2_data)
    await repository.create(calendar3_data)

    # Filter by user_id=1 and name="Work"
    filter = CalendarFilter(
        user_id=1,
        name="Work",
        url=None,
        limit=100,
        offset=0,
    )
    calendars = await repository.find(filter)
    assert len(calendars) == 1
    assert calendars[0].id == calendar1.id
    assert calendars[0].user_id == 1
    assert calendars[0].name == "Work"
