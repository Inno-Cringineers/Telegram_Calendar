"""Tests for Calendar model using mocks."""

import pytest

from models.calendar import Calendar


def test_calendar_creation_with_valid_data() -> None:
    """Test that Calendar can be created with valid data."""
    calendar = Calendar(
        user_id=12345,
        name="My Calendar",
        url="https://example.com/calendar.ics",
        sync_enabled=True,
    )

    assert calendar.user_id == 12345
    assert calendar.name == "My Calendar"
    assert calendar.url == "https://example.com/calendar.ics"
    assert calendar.sync_enabled is True
    assert calendar.last_sync is None


def test_calendar_name_constraint() -> None:
    """Tests validation of Calendar name."""

    # empty name
    with pytest.raises(ValueError):
        Calendar(name="")

    # name too long
    with pytest.raises(ValueError):
        Calendar(name="a" * 256)


def test_url_constraint() -> None:
    """Tests validation of Calendar URL."""

    # empty URL
    with pytest.raises(ValueError):
        Calendar(url="")

    # URL too long
    with pytest.raises(ValueError):
        Calendar(url="a" * 256)

    # URL with whitespace only
    with pytest.raises(ValueError):
        Calendar(url="   ")

    # URL without http or https
    with pytest.raises(ValueError):
        Calendar(url="example.com/calendar.ics")
