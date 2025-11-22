"""
Unit tests for SettingsRepository using TDD approach.

Tests cover:
- Creating settings
- Retrieving settings by ID
- Retrieving settings by user_id
- Updating settings
- Deleting settings
- Edge cases and validation
"""

from datetime import time
from typing import TYPE_CHECKING

import pytest
import pytest_asyncio
from sqlalchemy import select, text

from database.database import Base, get_engine, get_session_maker
from models.settings import Settings
from repositories.exceptions import SettingsNotFoundError
from repositories.schemas import SettingsCreateSchema, SettingsUpdateSchema

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from repositories.settings_repository import SettingsRepository


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
async def repository(session: "AsyncSession") -> "SettingsRepository":
    """Create SettingsRepository instance for tests.

    Note: Repository receives session directly, not through Store.
    This is the recommended approach - simple and explicit.
    """
    from repositories.settings_repository import SettingsRepository

    return SettingsRepository(session)


# ============================================================================
# CREATE OPERATIONS
# ============================================================================


@pytest.mark.asyncio
async def test_create_settings_success(repository: "SettingsRepository") -> None:
    """Test successful settings creation."""
    # Arrange
    settings_data = SettingsCreateSchema(
        user_id=1,
        timezone="UTC+2",
        language="ru",
        quiet_hours_start=None,
        quiet_hours_end=None,
        daily_plans_time=None,
        default_reminder_offset=15 * 60,
    )

    # Act
    settings = await repository.create(settings_data)

    # Assert
    assert settings.id is not None
    assert settings.user_id == 1
    assert settings.timezone == "UTC+2"
    assert settings.language == "ru"
    assert settings.default_reminder_offset == 15 * 60


@pytest.mark.asyncio
async def test_create_settings_with_quiet_hours(repository: "SettingsRepository") -> None:
    """Test settings creation with quiet hours."""
    # Arrange
    settings_data = SettingsCreateSchema(
        user_id=1,
        timezone="UTC+2",
        language="ru",
        quiet_hours_start=time(22, 0),
        quiet_hours_end=time(8, 0),
        daily_plans_time=None,
        default_reminder_offset=15 * 60,
    )

    # Act
    settings = await repository.create(settings_data)

    # Assert
    assert settings.quiet_hours_start == time(22, 0)
    assert settings.quiet_hours_end == time(8, 0)


@pytest.mark.asyncio
async def test_create_settings_with_daily_plans_time(repository: "SettingsRepository") -> None:
    """Test settings creation with daily plans time."""
    # Arrange
    settings_data = SettingsCreateSchema(
        user_id=1,
        timezone="UTC+2",
        language="ru",
        quiet_hours_start=None,
        quiet_hours_end=None,
        daily_plans_time=time(9, 0),
        default_reminder_offset=15 * 60,
    )

    # Act
    settings = await repository.create(settings_data)

    # Assert
    assert settings.daily_plans_time == time(9, 0)


@pytest.mark.asyncio
async def test_create_settings_with_all_fields(repository: "SettingsRepository") -> None:
    """Test settings creation with all fields filled."""
    # Arrange
    settings_data = SettingsCreateSchema(
        user_id=1,
        timezone="UTC+3",
        language="en",
        quiet_hours_start=time(23, 0),
        quiet_hours_end=time(7, 0),
        daily_plans_time=time(8, 30),
        default_reminder_offset=30 * 60,
    )

    # Act
    settings = await repository.create(settings_data)

    # Assert
    assert settings.timezone == "UTC+3"
    assert settings.language == "en"
    assert settings.quiet_hours_start == time(23, 0)
    assert settings.quiet_hours_end == time(7, 0)
    assert settings.daily_plans_time == time(8, 30)
    assert settings.default_reminder_offset == 30 * 60


@pytest.mark.asyncio
async def test_create_settings_with_minimal_data(repository: "SettingsRepository") -> None:
    """Test settings creation with minimal required data."""
    # Arrange
    settings_data = SettingsCreateSchema(
        user_id=1,
        timezone="UTC+2",
        language="ru",
        quiet_hours_start=None,
        quiet_hours_end=None,
        daily_plans_time=None,
        default_reminder_offset=15 * 60,
    )

    # Act
    settings = await repository.create(settings_data)

    # Assert
    assert settings.id is not None
    assert settings.user_id == 1
    assert settings.timezone == "UTC+2"
    assert settings.language == "ru"
    assert settings.quiet_hours_start is None
    assert settings.quiet_hours_end is None
    assert settings.daily_plans_time is None
    assert settings.default_reminder_offset == 15 * 60  # Default value


# ============================================================================
# READ OPERATIONS
# ============================================================================


@pytest.mark.asyncio
async def test_get_by_id_success(repository: "SettingsRepository", session: "AsyncSession") -> None:
    """Test retrieving settings by ID."""
    # Arrange
    settings = Settings(
        user_id=1,
        timezone="UTC+2",
        language="ru",
        default_reminder_offset=15 * 60,
    )
    session.add(settings)
    await session.flush()
    settings_id = settings.id

    # Act
    retrieved = await repository.get_by_id(settings_id)

    # Assert
    assert retrieved is not None
    assert retrieved.id == settings_id
    assert retrieved.user_id == 1
    assert retrieved.timezone == "UTC+2"


@pytest.mark.asyncio
async def test_get_by_id_not_found(repository: "SettingsRepository") -> None:
    """Test retrieving non-existent settings by ID."""
    # Arrange
    non_existent_id = 999

    # Act
    result = await repository.get_by_id(non_existent_id)

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_by_user_id_success(repository: "SettingsRepository", session: "AsyncSession") -> None:
    """Test retrieving settings by user ID."""
    # Arrange
    settings1 = Settings(
        user_id=1,
        timezone="UTC+2",
        language="ru",
        default_reminder_offset=15 * 60,
    )
    settings2 = Settings(
        user_id=2,
        timezone="UTC+3",
        language="en",
        default_reminder_offset=30 * 60,
    )
    session.add_all([settings1, settings2])
    await session.flush()

    # Act
    retrieved = await repository.get_by_user_id(1)

    # Assert
    assert retrieved is not None
    assert retrieved.user_id == 1
    assert retrieved.timezone == "UTC+2"
    assert retrieved.language == "ru"


@pytest.mark.asyncio
async def test_get_by_user_id_not_found(repository: "SettingsRepository") -> None:
    """Test retrieving settings for user with no settings."""
    # Arrange
    non_existent_user_id = 999

    # Act
    result = await repository.get_by_user_id(non_existent_user_id)

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_by_user_id_returns_single_result(repository: "SettingsRepository", session: "AsyncSession") -> None:
    """Test that get_by_user_id returns only one settings per user."""
    # Arrange
    settings1 = Settings(
        user_id=1,
        timezone="UTC+2",
        language="ru",
        default_reminder_offset=15 * 60,
    )
    session.add(settings1)
    await session.flush()

    # Act
    retrieved = await repository.get_by_user_id(1)

    # Assert
    assert retrieved is not None
    assert retrieved.id == settings1.id


# ============================================================================
# UPDATE OPERATIONS
# ============================================================================


@pytest.mark.asyncio
async def test_update_settings_success(repository: "SettingsRepository", session: "AsyncSession") -> None:
    """Test successful settings update."""
    # Arrange
    settings = Settings(
        user_id=1,
        timezone="UTC+2",
        language="ru",
        default_reminder_offset=15 * 60,
    )
    session.add(settings)
    await session.flush()
    settings_id = settings.id

    update_data = SettingsUpdateSchema(timezone="UTC+3", language="en")  # type: ignore[call-arg]

    # Act
    updated = await repository.update(settings_id, update_data)

    # Assert
    assert updated.timezone == "UTC+3"
    assert updated.language == "en"
    assert updated.id == settings_id
    assert updated.user_id == 1  # Should not change


@pytest.mark.asyncio
async def test_update_settings_not_found(repository: "SettingsRepository") -> None:
    """Test updating non-existent settings."""
    # Arrange
    non_existent_id = 999
    update_data = SettingsUpdateSchema(timezone="UTC+3")  # type: ignore[call-arg]

    # Act & Assert
    with pytest.raises(SettingsNotFoundError):
        await repository.update(non_existent_id, update_data)


@pytest.mark.asyncio
async def test_update_settings_partial(repository: "SettingsRepository", session: "AsyncSession") -> None:
    """Test partial settings update (only some fields)."""
    # Arrange
    settings = Settings(
        user_id=1,
        timezone="UTC+2",
        language="ru",
        default_reminder_offset=15 * 60,
    )
    session.add(settings)
    await session.flush()
    settings_id = settings.id

    update_data = SettingsUpdateSchema(timezone="UTC+3")  # type: ignore[call-arg]

    # Act
    updated = await repository.update(settings_id, update_data)

    # Assert
    assert updated.timezone == "UTC+3"
    assert updated.language == "ru"  # Unchanged
    assert updated.default_reminder_offset == 15 * 60  # Unchanged


@pytest.mark.asyncio
async def test_update_settings_with_quiet_hours(repository: "SettingsRepository", session: "AsyncSession") -> None:
    """Test updating settings with quiet hours."""
    # Arrange
    settings = Settings(
        user_id=1,
        timezone="UTC+2",
        language="ru",
        default_reminder_offset=15 * 60,
    )
    session.add(settings)
    await session.flush()
    settings_id = settings.id

    update_data = SettingsUpdateSchema(
        quiet_hours_start=time(22, 0),
        quiet_hours_end=time(8, 0),  # type: ignore[call-arg]
    )

    # Act
    updated = await repository.update(settings_id, update_data)

    # Assert
    assert updated.quiet_hours_start == time(22, 0)
    assert updated.quiet_hours_end == time(8, 0)


@pytest.mark.asyncio
async def test_update_settings_with_daily_plans_time(repository: "SettingsRepository", session: "AsyncSession") -> None:
    """Test updating settings with daily plans time."""
    # Arrange
    settings = Settings(
        user_id=1,
        timezone="UTC+2",
        language="ru",
        default_reminder_offset=15 * 60,
    )
    session.add(settings)
    await session.flush()
    settings_id = settings.id

    update_data = SettingsUpdateSchema(daily_plans_time=time(9, 0))  # type: ignore[call-arg]

    # Act
    updated = await repository.update(settings_id, update_data)

    # Assert
    assert updated.daily_plans_time == time(9, 0)


@pytest.mark.asyncio
async def test_update_all_fields(repository: "SettingsRepository", session: "AsyncSession") -> None:
    """Test updating all fields of settings."""
    # Arrange
    settings = Settings(
        user_id=1,
        timezone="UTC+2",
        language="ru",
        quiet_hours_start=None,
        quiet_hours_end=None,
        daily_plans_time=None,
        default_reminder_offset=15 * 60,
    )
    session.add(settings)
    await session.flush()
    settings_id = settings.id

    update_data = SettingsUpdateSchema(
        timezone="UTC+5",
        language="en",
        quiet_hours_start=time(23, 0),
        quiet_hours_end=time(7, 0),
        daily_plans_time=time(8, 30),
        default_reminder_offset=30 * 60,
    )

    # Act
    updated = await repository.update(settings_id, update_data)

    # Assert
    assert updated.timezone == "UTC+5"
    assert updated.language == "en"
    assert updated.quiet_hours_start == time(23, 0)
    assert updated.quiet_hours_end == time(7, 0)
    assert updated.daily_plans_time == time(8, 30)
    assert updated.default_reminder_offset == 30 * 60


@pytest.mark.asyncio
async def test_update_with_none_values(repository: "SettingsRepository", session: "AsyncSession") -> None:
    """Test that updating with None values doesn't clear fields (None means don't update)."""
    # Arrange
    settings = Settings(
        user_id=1,
        timezone="UTC+2",
        language="ru",
        quiet_hours_start=time(22, 0),
        quiet_hours_end=time(8, 0),
        daily_plans_time=time(9, 0),
        default_reminder_offset=15 * 60,
    )
    session.add(settings)
    await session.flush()
    settings_id = settings.id

    # Update with no fields set (empty schema) - should not change anything
    # Pydantic's exclude_unset=True means None values are excluded if not explicitly set
    update_data = SettingsUpdateSchema()  # Empty update - no fields set  # type: ignore[call-arg]

    # Act
    updated = await repository.update(settings_id, update_data)

    # Assert
    assert updated.timezone == "UTC+2"  # Unchanged
    assert updated.language == "ru"  # Unchanged
    assert updated.quiet_hours_start == time(22, 0)  # Unchanged
    assert updated.quiet_hours_end == time(8, 0)  # Unchanged
    assert updated.daily_plans_time == time(9, 0)  # Unchanged


# ============================================================================
# DELETE OPERATIONS
# ============================================================================


@pytest.mark.asyncio
async def test_delete_settings_success(repository: "SettingsRepository", session: "AsyncSession") -> None:
    """Test successful settings deletion."""
    # Arrange
    settings = Settings(
        user_id=1,
        timezone="UTC+2",
        language="ru",
        default_reminder_offset=15 * 60,
    )
    session.add(settings)
    await session.flush()
    settings_id = settings.id

    # Act
    await repository.delete(settings_id)

    # Assert
    result = await session.execute(select(Settings).where(Settings.id == settings_id))
    assert result.scalar() is None


@pytest.mark.asyncio
async def test_delete_settings_not_found(repository: "SettingsRepository") -> None:
    """Test deleting non-existent settings."""
    # Arrange
    non_existent_id = 999

    # Act & Assert
    with pytest.raises(SettingsNotFoundError):
        await repository.delete(non_existent_id)


# ============================================================================
# EDGE CASES AND VALIDATION
# ============================================================================


@pytest.mark.asyncio
async def test_create_settings_with_default_reminder_offset(repository: "SettingsRepository") -> None:
    """Test settings creation with default reminder offset."""
    # Arrange
    settings_data = SettingsCreateSchema(
        user_id=1,
        timezone="UTC+2",
        language="ru",
        quiet_hours_start=None,
        quiet_hours_end=None,
        daily_plans_time=None,
        default_reminder_offset=30 * 60,
    )

    # Act
    settings = await repository.create(settings_data)

    # Assert
    assert settings.default_reminder_offset == 30 * 60


@pytest.mark.asyncio
async def test_update_settings_clear_quiet_hours(repository: "SettingsRepository", session: "AsyncSession") -> None:
    """Test clearing quiet hours by setting both to None."""
    # Arrange
    settings = Settings(
        user_id=1,
        timezone="UTC+2",
        language="ru",
        quiet_hours_start=time(22, 0),
        quiet_hours_end=time(8, 0),
        default_reminder_offset=15 * 60,
    )
    session.add(settings)
    await session.flush()
    settings_id = settings.id

    update_data = SettingsUpdateSchema(quiet_hours_start=None, quiet_hours_end=None)  # type: ignore[call-arg]

    # Act
    updated = await repository.update(settings_id, update_data)

    # Assert
    assert updated.quiet_hours_start is None
    assert updated.quiet_hours_end is None


@pytest.mark.asyncio
async def test_update_settings_clear_daily_plans_time(
    repository: "SettingsRepository", session: "AsyncSession"
) -> None:
    """Test clearing daily plans time by setting to None."""
    # Arrange
    settings = Settings(
        user_id=1,
        timezone="UTC+2",
        language="ru",
        daily_plans_time=time(9, 0),
        default_reminder_offset=15 * 60,
    )
    session.add(settings)
    await session.flush()
    settings_id = settings.id

    update_data = SettingsUpdateSchema(daily_plans_time=None)  # type: ignore[call-arg]

    # Act
    updated = await repository.update(settings_id, update_data)

    # Assert
    assert updated.daily_plans_time is None


@pytest.mark.asyncio
async def test_create_multiple_settings_for_different_users(
    repository: "SettingsRepository", session: "AsyncSession"
) -> None:
    """Test creating settings for multiple users."""
    # Arrange
    settings1_data = SettingsCreateSchema(
        user_id=1,
        timezone="UTC+2",
        language="ru",
        quiet_hours_start=None,
        quiet_hours_end=None,
        daily_plans_time=None,
        default_reminder_offset=15 * 60,
    )
    settings2_data = SettingsCreateSchema(
        user_id=2,
        timezone="UTC+3",
        language="en",
        quiet_hours_start=None,
        quiet_hours_end=None,
        daily_plans_time=None,
        default_reminder_offset=15 * 60,
    )

    # Act
    settings1 = await repository.create(settings1_data)
    settings2 = await repository.create(settings2_data)

    # Assert
    assert settings1.user_id == 1
    assert settings2.user_id == 2
    assert settings1.id != settings2.id

    # Verify both can be retrieved
    retrieved1 = await repository.get_by_user_id(1)
    retrieved2 = await repository.get_by_user_id(2)
    assert retrieved1 is not None
    assert retrieved2 is not None
    assert retrieved1.id == settings1.id
    assert retrieved2.id == settings2.id


@pytest.mark.asyncio
async def test_update_default_reminder_offset(repository: "SettingsRepository", session: "AsyncSession") -> None:
    """Test updating default reminder offset."""
    # Arrange
    settings = Settings(
        user_id=1,
        timezone="UTC+2",
        language="ru",
        default_reminder_offset=15 * 60,
    )
    session.add(settings)
    await session.flush()
    settings_id = settings.id

    update_data = SettingsUpdateSchema(default_reminder_offset=60 * 60)  # type: ignore[call-arg]

    # Act
    updated = await repository.update(settings_id, update_data)

    # Assert
    assert updated.default_reminder_offset == 60 * 60


@pytest.mark.asyncio
async def test_create_settings_with_zero_reminder_offset(repository: "SettingsRepository") -> None:
    """Test creating settings with zero reminder offset."""
    # Arrange
    settings_data = SettingsCreateSchema(
        user_id=1,
        timezone="UTC+2",
        language="ru",
        quiet_hours_start=None,
        quiet_hours_end=None,
        daily_plans_time=None,
        default_reminder_offset=0,
    )

    # Act
    settings = await repository.create(settings_data)

    # Assert
    assert settings.default_reminder_offset == 0
