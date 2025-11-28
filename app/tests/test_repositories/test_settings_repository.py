"""Tests for SettingsRepository using mocks."""

from datetime import time
from unittest.mock import AsyncMock, MagicMock

import pytest

from models.settings import Settings
from repositories.exceptions import SettingsNotFoundError
from repositories.schemas import SettingsCreateSchema, SettingsUpdateSchema
from repositories.settings_repository import SettingsRepository


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
def settings_repository(mock_session: AsyncMock) -> SettingsRepository:
    """Create a SettingsRepository instance with mocked session."""
    return SettingsRepository(mock_session)


@pytest.fixture
def sample_settings() -> Settings:
    """Create a sample Settings instance for testing."""
    settings = Settings(
        user_id=12345,
        timezone="UTC+2",
        language="en",
        quiet_hours=False,
        quiet_hours_start=time(hour=0, minute=0),
        quiet_hours_end=time(hour=6, minute=0),
        daily_plans_time=time(hour=9, minute=0),
        default_reminder_offset=15 * 60,
    )
    # Set id manually for testing (normally set by database)
    settings.id = 1
    return settings


@pytest.mark.asyncio
async def test_get_by_id_returns_settings(
    settings_repository: SettingsRepository, mock_session: AsyncMock, sample_settings: Settings
) -> None:
    """Test that get_by_id returns settings when found."""
    mock_session.get.return_value = sample_settings

    result = await settings_repository.get_by_id(1)

    assert result is sample_settings
    mock_session.get.assert_called_once_with(Settings, 1)


@pytest.mark.asyncio
async def test_get_by_id_returns_none_when_not_found(
    settings_repository: SettingsRepository, mock_session: AsyncMock
) -> None:
    """Test that get_by_id returns None when settings not found."""
    mock_session.get.return_value = None

    result = await settings_repository.get_by_id(999)

    assert result is None
    mock_session.get.assert_called_once_with(Settings, 999)


@pytest.mark.asyncio
async def test_create_creates_settings(settings_repository: SettingsRepository, mock_session: AsyncMock) -> None:
    """Test that create creates a new settings."""
    create_data = SettingsCreateSchema(  # type: ignore[call-arg]
        user_id=12345,
        timezone="UTC+3",
        language="ru",
        quiet_hours=True,
        quiet_hours_start=time(hour=22, minute=0),
        quiet_hours_end=time(hour=8, minute=0),
        daily_plans_time=time(hour=10, minute=30),
        default_reminder_offset=30 * 60,
    )

    result = await settings_repository.create(create_data)

    assert isinstance(result, Settings)
    assert result.user_id == 12345
    assert result.timezone == "UTC+3"
    assert result.language == "ru"
    assert result.quiet_hours is True
    assert result.quiet_hours_start == time(hour=22, minute=0)
    assert result.quiet_hours_end == time(hour=8, minute=0)
    assert result.daily_plans_time == time(hour=10, minute=30)
    assert result.default_reminder_offset == 30 * 60
    mock_session.add.assert_called_once_with(result)
    mock_session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_create_creates_settings_with_defaults(
    settings_repository: SettingsRepository, mock_session: AsyncMock
) -> None:
    """Test that create creates settings with default values."""
    create_data = SettingsCreateSchema(user_id=12345)  # type: ignore[call-arg]

    result = await settings_repository.create(create_data)

    assert isinstance(result, Settings)
    assert result.user_id == 12345
    assert result.timezone == "UTC+2"  # Default
    assert result.language == "en"  # Default
    assert result.quiet_hours is False  # Default
    assert result.quiet_hours_start == time(hour=0, minute=0)  # Default
    assert result.quiet_hours_end == time(hour=6, minute=0)  # Default
    assert result.daily_plans_time == time(hour=9, minute=0)  # Default
    assert result.default_reminder_offset == 15 * 60  # Default


@pytest.mark.asyncio
async def test_update_updates_existing_settings(
    settings_repository: SettingsRepository, mock_session: AsyncMock, sample_settings: Settings
) -> None:
    """Test that update updates an existing settings."""
    mock_session.get.return_value = sample_settings
    update_data = SettingsUpdateSchema(timezone="UTC+5")  # type: ignore[call-arg]

    result = await settings_repository.update(1, update_data)

    assert result is sample_settings
    assert result.timezone == "UTC+5"
    mock_session.get.assert_called_once_with(Settings, 1)
    mock_session.flush.assert_called_once()
    mock_session.refresh.assert_called_once_with(sample_settings)


@pytest.mark.asyncio
async def test_update_updates_multiple_fields(
    settings_repository: SettingsRepository, mock_session: AsyncMock, sample_settings: Settings
) -> None:
    """Test that update can update multiple fields."""
    mock_session.get.return_value = sample_settings
    update_data = SettingsUpdateSchema(  # type: ignore[call-arg]
        timezone="UTC+5", language="ru", quiet_hours=True, default_reminder_offset=60 * 60
    )

    result = await settings_repository.update(1, update_data)

    assert result.timezone == "UTC+5"
    assert result.language == "ru"
    assert result.quiet_hours is True
    assert result.default_reminder_offset == 60 * 60


@pytest.mark.asyncio
async def test_update_raises_error_when_settings_not_found(
    settings_repository: SettingsRepository, mock_session: AsyncMock
) -> None:
    """Test that update raises SettingsNotFoundError when settings not found."""
    mock_session.get.return_value = None
    update_data = SettingsUpdateSchema(timezone="UTC+5")  # type: ignore[call-arg]

    with pytest.raises(SettingsNotFoundError) as exc_info:
        await settings_repository.update(999, update_data)

    assert exc_info.value.settings_id == 999
    mock_session.get.assert_called_once_with(Settings, 999)
    mock_session.flush.assert_not_called()


@pytest.mark.asyncio
async def test_update_only_updates_provided_fields(
    settings_repository: SettingsRepository, mock_session: AsyncMock, sample_settings: Settings
) -> None:
    """Test that update only updates fields provided in schema."""
    original_timezone = sample_settings.timezone
    original_language = sample_settings.language
    mock_session.get.return_value = sample_settings
    update_data = SettingsUpdateSchema(quiet_hours=True)  # type: ignore[call-arg]

    result = await settings_repository.update(1, update_data)

    assert result.timezone == original_timezone  # Not changed
    assert result.language == original_language  # Not changed
    assert result.quiet_hours is True  # Changed
    mock_session.flush.assert_called_once()
    mock_session.refresh.assert_called_once_with(sample_settings)


@pytest.mark.asyncio
async def test_find_returns_settings_by_user_id(
    settings_repository: SettingsRepository, mock_session: AsyncMock, sample_settings: Settings
) -> None:
    """Test that find returns settings when found by user_id."""
    mock_result = MagicMock()
    mock_result.scalar.return_value = sample_settings
    mock_session.execute.return_value = mock_result

    result = await settings_repository.find(12345)

    assert result is sample_settings
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_find_returns_none_when_not_found(
    settings_repository: SettingsRepository, mock_session: AsyncMock
) -> None:
    """Test that find returns None when settings not found by user_id."""
    mock_result = MagicMock()
    mock_result.scalar.return_value = None
    mock_session.execute.return_value = mock_result

    result = await settings_repository.find(99999)

    assert result is None
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_delete_deletes_settings(
    settings_repository: SettingsRepository, mock_session: AsyncMock, sample_settings: Settings
) -> None:
    """Test that delete deletes an existing settings."""
    mock_session.get.return_value = sample_settings

    await settings_repository.delete(1)

    mock_session.get.assert_called_once_with(Settings, 1)
    mock_session.delete.assert_called_once_with(sample_settings)
    mock_session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_delete_raises_error_when_settings_not_found(
    settings_repository: SettingsRepository, mock_session: AsyncMock
) -> None:
    """Test that delete raises SettingsNotFoundError when settings not found."""
    mock_session.get.return_value = None

    with pytest.raises(SettingsNotFoundError) as exc_info:
        await settings_repository.delete(999)

    assert exc_info.value.settings_id == 999
    mock_session.get.assert_called_once_with(Settings, 999)
    mock_session.delete.assert_not_called()
    mock_session.flush.assert_not_called()
