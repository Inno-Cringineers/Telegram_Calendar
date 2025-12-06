"""Tests for Reminder model using mocks."""

import pytest

from models.reminder import Reminder


def get_correct_reminder_data() -> Reminder:
    return Reminder(
        event_id=1,
        description="Test description",
        trigger_offset="-P1D",
        sent=False,
    )


def test_reminder_creation_with_correct_data() -> None:
    """Test that Reminder can be created with minimal required data."""
    reminder = get_correct_reminder_data()

    assert reminder.event_id == 1
    assert reminder.description == "Test description"
    assert reminder.trigger_offset == "-P1D"
    assert reminder.sent is False


def test_description_constraint() -> None:
    """Test that Reminder description validation constraints."""

    reminder = get_correct_reminder_data()

    # description too long
    with pytest.raises(ValueError, match="description cannot exceed 1024 characters"):
        reminder.description = "a" * 1025
