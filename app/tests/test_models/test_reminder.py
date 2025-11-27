"""
Unit tests for the Remider model.

Tests cover:
- ORM-level validation (ValueError)
- SQL-level constraints (IntegrityError)
- Default values
"""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.database import Base
from models.event import Event
from models.reminder import Reminder, compute_remind_at


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


# ---------------------------------------------------------------------------
# HELPER FUNCTION TESTS
# ---------------------------------------------------------------------------


def test_compute_remind_at_basic():
    # Arrange
    start = datetime(2025, 11, 20, 12, 0, tzinfo=UTC)

    class DummyEvent:
        date_start = start
        reminder_offset = 600  # 10 minutes

    event = DummyEvent()

    # Act
    remind = compute_remind_at(event)

    # Assert
    assert remind == start - timedelta(seconds=600)


def test_compute_remind_at_invalid_offset_type():
    # Arrange
    start = datetime(2025, 11, 20, 12, 0, tzinfo=UTC)

    class DummyEvent:
        date_start = start
        reminder_offset = "10"

    event = DummyEvent()

    # Act & Assert
    with pytest.raises(ValueError):
        compute_remind_at(event)


def test_compute_remind_at_naive_datetime():
    # Arrange
    start = datetime(2025, 11, 20, 12, 0)  # naive

    class DummyEvent:
        date_start = start
        reminder_offset = 600

    event = DummyEvent()

    # Act & Assert
    with pytest.raises(ValueError):
        compute_remind_at(event)


def test_compute_remind_at_future_remind():
    # Arrange
    start = datetime(2025, 11, 20, 12, 0, tzinfo=UTC)

    class DummyEvent:
        date_start = start
        reminder_offset = -10  # negative offset -> reminder after start

    event = DummyEvent()

    # Act & Assert
    with pytest.raises(ValueError):
        compute_remind_at(event)


# ---------------------------------------------------------------------------
# ORM / MODEL TESTS
# ---------------------------------------------------------------------------


def test_create_reminder(session):
    # Arrange
    start = datetime(2025, 11, 20, 12, 0, tzinfo=UTC)
    end = start + timedelta(hours=1)
    event = Event(user_id=1, title="Test Event", date_start=start, date_end=end, reminder_offset=600)
    session.add(event)
    session.flush()

    # Act
    reminder = Reminder(user_id=1, event_id=event.id, event=event, remind_at=compute_remind_at(event))
    session.add(reminder)
    session.flush()

    # Assert
    assert reminder.sent is False
    assert reminder.remind_at == start - timedelta(seconds=600)
    assert reminder.event_id == event.id


def test_remind_at_must_be_datetime(session):
    # Arrange
    start = datetime(2025, 11, 20, 12, 0, tzinfo=UTC)
    end = start + timedelta(hours=1)
    event = Event(user_id=1, title="Event", date_start=start, date_end=end, reminder_offset=600)
    session.add(event)
    session.flush()

    # Act & Assert
    with pytest.raises(ValueError):
        reminder = Reminder(user_id=1, event_id=event.id, event=event, remind_at="not a datetime")
        session.add(reminder)
        session.flush()


def test_remind_at_must_be_timezone_aware(session):
    # Arrange
    start = datetime(2025, 11, 20, 12, 0, tzinfo=UTC)
    end = start + timedelta(hours=1)
    event = Event(user_id=1, title="Event", date_start=start, date_end=end, reminder_offset=600)
    session.add(event)
    session.flush()

    naive_dt = datetime(2025, 11, 20, 11, 50)  # naive datetime

    # Act & Assert
    with pytest.raises(ValueError):
        reminder = Reminder(user_id=1, event_id=event.id, event=event, remind_at=naive_dt)
        session.add(reminder)
        session.flush()


def test_reminder_not_after_event_start(session):
    # Arrange
    start = datetime(2025, 11, 20, 12, 0, tzinfo=UTC)
    end = start + timedelta(hours=1)
    event = Event(user_id=1, title="Event", date_start=start, date_end=end, reminder_offset=600)
    session.add(event)
    session.flush()

    future_remind = start + timedelta(minutes=1)  # remind_at after event start should fail

    # Act & Assert
    with pytest.raises(ValueError):
        reminder = Reminder(user_id=1, event_id=event.id, event=event, remind_at=future_remind)
        session.add(reminder)
        session.flush()


def test_sent_default_false(session):
    # Arrange
    start = datetime(2025, 11, 20, 12, 0, tzinfo=UTC)
    end = start + timedelta(hours=1)
    event = Event(user_id=1, title="Event", date_start=start, date_end=end, reminder_offset=600)
    session.add(event)
    session.flush()

    # Act
    reminder = Reminder(user_id=1, event_id=event.id, event=event, remind_at=compute_remind_at(event))
    session.add(reminder)
    session.flush()

    # Assert
    assert reminder.sent is False
