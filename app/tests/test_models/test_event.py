"""Tests for Event model using mocks."""

from datetime import UTC, datetime

import pytest

from models.event import Event


def get_correct_event_data() -> Event:
    return Event(
        user_id=12345,
        uid="event-123",
        calendar_id=1,
        date_start=datetime(2025, 1, 1, 10, 0, tzinfo=UTC),
        date_end=datetime(2025, 1, 1, 11, 0, tzinfo=UTC),
        all_day=False,
        need_to_remind=True,
        title="Test Event",
        description="Test description",
        rrule="FREQ=DAILY;COUNT=10",
        rdate=[datetime(2025, 1, 2, 10, 0, tzinfo=UTC)],
        exdate=[datetime(2025, 1, 3, 10, 0, tzinfo=UTC)],
    )


def test_event_creation_with_correct_data() -> None:
    """Test that Event can be created with correct data."""
    event = get_correct_event_data()

    assert event.user_id == 12345
    assert event.uid == "event-123"
    assert event.calendar_id == 1
    assert event.date_start == datetime(2025, 1, 1, 10, 0, tzinfo=UTC)
    assert event.date_end == datetime(2025, 1, 1, 11, 0, tzinfo=UTC)
    assert event.all_day is False
    assert event.need_to_remind is True
    assert event.title == "Test Event"
    assert event.description == "Test description"
    assert event.rrule == "FREQ=DAILY;COUNT=10"
    assert event.rdate == [datetime(2025, 1, 2, 10, 0, tzinfo=UTC)]
    assert event.exdate == [datetime(2025, 1, 3, 10, 0, tzinfo=UTC)]


def test_event_title_constraint() -> None:
    """Test that Event title validation constraints."""

    event = get_correct_event_data()

    # empty title
    with pytest.raises(ValueError, match="Event title \\(SUMMARY\\) cannot be empty"):
        event.title = ""

    # title too long
    with pytest.raises(ValueError, match="Event title \\(SUMMARY\\) cannot exceed 255 characters"):
        event.title = "a" * 256


def test_event_date_end_constraint() -> None:
    """Test that Event date end validation constraints."""

    event = get_correct_event_data()

    # date end is before start
    with pytest.raises(ValueError, match="Event end date \\(DTEND\\) must be not before start date \\(DTSTART\\)."):
        event.date_end = datetime(2025, 1, 1, 9, 0, tzinfo=UTC)
