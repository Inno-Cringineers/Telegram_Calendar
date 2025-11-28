"""Tests for Reminder model using mocks."""

from datetime import UTC, datetime

import pytest

from models.reminder import Reminder


def get_correct_reminder_data() -> Reminder:
    return Reminder(
        event_id=1,
        description="Test description",
        trigger_offset="-P1D",
        trigger_datetime=datetime(2025, 1, 1, 10, 0, tzinfo=UTC),
        repeat_count=3,
        repeat_interval="PT10M",
        sent=False,
    )


def test_reminder_creation_with_correct_data() -> None:
    """Test that Reminder can be created with minimal required data."""
    reminder = get_correct_reminder_data()

    assert reminder.event_id == 1
    assert reminder.description == "Test description"
    assert reminder.trigger_offset == "-P1D"
    assert reminder.trigger_datetime == datetime(2025, 1, 1, 10, 0, tzinfo=UTC)
    assert reminder.repeat_count == 3
    assert reminder.repeat_interval == "PT10M"
    assert reminder.sent is False


def test_description_constraint() -> None:
    """Test that Reminder description validation constraints."""

    reminder = get_correct_reminder_data()

    # description too long
    with pytest.raises(ValueError, match="description cannot exceed 1024 characters"):
        reminder.description = "a" * 1025


def test_repeat_count_constraint() -> None:
    """Test that Reminder repeat count validation constraints."""

    reminder = get_correct_reminder_data()

    # repeat count is negative
    with pytest.raises(ValueError, match="repeat_count cannot be negative"):
        reminder.repeat_count = -1
