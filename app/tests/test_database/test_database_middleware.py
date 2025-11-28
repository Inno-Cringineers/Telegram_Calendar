"""Tests for DatabaseMiddleware using mocks."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from middlewares.database_middlware import DatabaseMiddleware


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
async def test_middleware_injects_session_and_commits(mock_session_maker: MagicMock, mock_session: AsyncMock) -> None:
    """Ensure middleware injects session and commits when handler completes."""
    mw = DatabaseMiddleware(mock_session_maker)

    handler_result = "ok"
    handler_called = False

    async def handler(event: Any, data: dict[str, Any]) -> str:
        nonlocal handler_called
        handler_called = True
        # Verify session is injected
        assert "session" in data
        assert data["session"] is mock_session
        return handler_result

    event = MagicMock()
    data: dict[str, Any] = {}

    result = await mw(handler, event=event, data=data)

    # Verify handler was called and result is returned
    assert handler_called
    assert result == handler_result

    # Verify session was injected into data
    assert "session" in data
    assert data["session"] is mock_session

    # Verify UnitOfWork behavior: begin, commit, close (no rollback)
    mock_session.begin.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.rollback.assert_not_called()
    mock_session.close.assert_called_once()
    mock_session_maker.assert_called_once()


@pytest.mark.asyncio
async def test_middleware_rolls_back_on_handler_exception(
    mock_session_maker: MagicMock, mock_session: AsyncMock
) -> None:
    """Handler raises -> UnitOfWork must rollback and exception must propagate."""
    mw = DatabaseMiddleware(mock_session_maker)

    class TestException(Exception):
        """Test exception for rollback testing."""

    handler_called = False

    async def bad_handler(event: Any, data: dict[str, Any]) -> None:
        nonlocal handler_called
        handler_called = True
        # Verify session is injected before exception
        assert "session" in data
        assert data["session"] is mock_session
        raise TestException("Handler error")

    event = MagicMock()
    data: dict[str, Any] = {}

    # Exception should propagate
    with pytest.raises(TestException, match="Handler error"):
        await mw(bad_handler, event=event, data=data)

    # Verify handler was called
    assert handler_called

    # Verify UnitOfWork behavior: begin, rollback, close (no commit)
    mock_session.begin.assert_called_once()
    mock_session.rollback.assert_called_once()
    mock_session.commit.assert_not_called()
    mock_session.close.assert_called_once()


@pytest.mark.asyncio
async def test_middleware_passes_event_to_handler(mock_session_maker: MagicMock, mock_session: AsyncMock) -> None:
    """Test that middleware correctly passes event to handler."""
    mw = DatabaseMiddleware(mock_session_maker)

    received_event = None

    async def handler(event: Any, data: dict[str, Any]) -> str:
        nonlocal received_event
        received_event = event
        return "success"

    test_event = MagicMock()
    data: dict[str, Any] = {}

    result = await mw(handler, event=test_event, data=data)

    assert result == "success"
    assert received_event is test_event


@pytest.mark.asyncio
async def test_middleware_preserves_data_dict(mock_session_maker: MagicMock, mock_session: AsyncMock) -> None:
    """Test that middleware preserves existing data in data dict."""
    mw = DatabaseMiddleware(mock_session_maker)

    async def handler(event: Any, data: dict[str, Any]) -> str:
        # Verify existing data is preserved
        assert data["existing_key"] == "existing_value"
        assert "session" in data
        return "success"

    event = MagicMock()
    data: dict[str, Any] = {"existing_key": "existing_value"}

    result = await mw(handler, event=event, data=data)

    assert result == "success"
    # Verify existing data is still there
    assert data["existing_key"] == "existing_value"
    assert data["session"] is mock_session
