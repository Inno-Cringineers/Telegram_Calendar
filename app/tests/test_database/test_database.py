"""Unit tests for database utils and UnitOfWork."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from database.database import UnitOfWork, normalize_db_url


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("postgresql+asyncpg://user:pass@localhost/db", "postgresql+asyncpg://user:pass@localhost/db"),
        ("postgresql://user:pass@localhost/db", "postgresql+asyncpg://user:pass@localhost/db"),
    ],
)
def test_normalize_db_url(url: str, expected: str) -> None:
    """Test normalize_db_url function with various URL formats."""
    assert normalize_db_url(url) == expected


@pytest.fixture
def mock_session() -> AsyncMock:
    """Create a mock AsyncSession."""
    session = AsyncMock()
    session.begin = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def mock_session_maker(mock_session: AsyncMock) -> MagicMock:
    """Create a mock async_sessionmaker that returns the mock session."""
    session_maker = MagicMock()
    session_maker.return_value = mock_session
    return session_maker


@pytest.mark.asyncio
async def test_uow_commit_persists(mock_session_maker: MagicMock, mock_session: AsyncMock) -> None:
    """Test that UnitOfWork commits transaction on successful exit."""
    uow = UnitOfWork(mock_session_maker)

    async with uow as session:
        assert session is mock_session
        # Verify session.begin was called
        mock_session.begin.assert_called_once()

    # Verify commit was called (not rollback)
    mock_session.commit.assert_called_once()
    mock_session.rollback.assert_not_called()
    mock_session.close.assert_called_once()
    mock_session_maker.assert_called_once()


@pytest.mark.asyncio
async def test_uow_rollback_on_exception(mock_session_maker: MagicMock, mock_session: AsyncMock) -> None:
    """Test that UnitOfWork rolls back transaction on exception."""
    uow = UnitOfWork(mock_session_maker)

    class TestException(Exception):
        """Test exception for rollback testing."""

    with pytest.raises(TestException):
        async with uow as session:
            assert session is mock_session
            mock_session.begin.assert_called_once()
            raise TestException("Test error")

    # Verify rollback was called (not commit)
    mock_session.rollback.assert_called_once()
    mock_session.commit.assert_not_called()
    mock_session.close.assert_called_once()


@pytest.mark.asyncio
async def test_uow_direct_usage(mock_session_maker: MagicMock, mock_session: AsyncMock) -> None:
    """Test that UnitOfWork works with manual commit."""
    uow = UnitOfWork(mock_session_maker)

    async with uow as session:
        assert session is mock_session
        mock_session.begin.assert_called_once()
        # Manual commit inside context
        await session.commit()

    # Verify commit was called (both manual and automatic)
    assert mock_session.commit.call_count == 2
    mock_session.rollback.assert_not_called()
    mock_session.close.assert_called_once()


@pytest.mark.asyncio
async def test_uow_session_not_created_error(mock_session_maker: MagicMock) -> None:
    """Test that UnitOfWork raises error if session was not created."""
    uow = UnitOfWork(mock_session_maker)
    # Manually set session to None to simulate error
    uow.session = None

    with pytest.raises(RuntimeError, match="UnitOfWork session was not created"):
        await uow.__aexit__(None, None, None)


@pytest.mark.asyncio
async def test_uow_begin_called(mock_session_maker: MagicMock, mock_session: AsyncMock) -> None:
    """Test that UnitOfWork calls begin() on session entry."""
    uow = UnitOfWork(mock_session_maker)

    async with uow:
        mock_session.begin.assert_called_once()


@pytest.mark.asyncio
async def test_uow_close_always_called(mock_session_maker: MagicMock, mock_session: AsyncMock) -> None:
    """Test that UnitOfWork always closes session, even if commit/rollback fails."""
    uow = UnitOfWork(mock_session_maker)
    # Make commit raise an exception
    mock_session.commit.side_effect = Exception("Commit failed")

    # Exception from commit should be raised, but close should still be called
    with pytest.raises(Exception, match="Commit failed"):
        async with uow:
            pass

    # Even though commit failed, close should still be called (in finally block)
    mock_session.close.assert_called_once()
