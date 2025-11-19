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

from bot.database.database import Base
from bot.models.event import Event
from bot.models.reminder import Reminder, compute_remind_at


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
    start = datetime(2025, 11, 20, 12, 0, tzinfo=UTC)

    class DummyEvent:
        date_start = start
        reminder_offset = 600  # 10 minutes

    event = DummyEvent()
    remind = compute_remind_at(event)
    assert remind == start - timedelta(seconds=600)


def test_compute_remind_at_invalid_offset_type():
    start = datetime(2025, 11, 20, 12, 0, tzinfo=UTC)

    class DummyEvent:
        date_start = start
        reminder_offset = "10"

    event = DummyEvent()
    with pytest.raises(ValueError):
        compute_remind_at(event)


def test_compute_remind_at_naive_datetime():
    start = datetime(2025, 11, 20, 12, 0)  # naive

    class DummyEvent:
        date_start = start
        reminder_offset = 600

    event = DummyEvent()
    with pytest.raises(ValueError):
        compute_remind_at(event)


def test_compute_remind_at_future_remind():
    start = datetime(2025, 11, 20, 12, 0, tzinfo=UTC)

    class DummyEvent:
        date_start = start
        reminder_offset = -10  # negative offset -> reminder after start

    event = DummyEvent()
    with pytest.raises(ValueError):
        compute_remind_at(event)


# ---------------------------------------------------------------------------
# ORM / MODEL TESTS
# ---------------------------------------------------------------------------


def test_create_reminder(session):
    start = datetime(2025, 11, 20, 12, 0, tzinfo=UTC)
    end = start + timedelta(hours=1)
    event = Event(user_id=1, title="Test Event", date_start=start, date_end=end, reminder_offset=600)
    session.add(event)
    session.flush()

    reminder = Reminder(user_id=1, event_id=event.id, event=event, remind_at=compute_remind_at(event))
    session.add(reminder)
    session.flush()

    assert reminder.sent is False
    assert reminder.remind_at == start - timedelta(seconds=600)
    assert reminder.event_id == event.id


def test_remind_at_must_be_datetime(session):
    start = datetime(2025, 11, 20, 12, 0, tzinfo=UTC)
    end = start + timedelta(hours=1)
    event = Event(user_id=1, title="Event", date_start=start, date_end=end, reminder_offset=600)
    session.add(event)
    session.flush()

    with pytest.raises(ValueError):
        reminder = Reminder(user_id=1, event_id=event.id, event=event, remind_at="not a datetime")
        session.add(reminder)
        session.flush()


def test_remind_at_must_be_timezone_aware(session):
    start = datetime(2025, 11, 20, 12, 0, tzinfo=UTC)
    end = start + timedelta(hours=1)
    event = Event(user_id=1, title="Event", date_start=start, date_end=end, reminder_offset=600)
    session.add(event)
    session.flush()

    naive_dt = datetime(2025, 11, 20, 11, 50)  # naive datetime
    with pytest.raises(ValueError):
        reminder = Reminder(user_id=1, event_id=event.id, event=event, remind_at=naive_dt)
        session.add(reminder)
        session.flush()


def test_reminder_not_after_event_start(session):
    start = datetime(2025, 11, 20, 12, 0, tzinfo=UTC)
    end = start + timedelta(hours=1)
    event = Event(user_id=1, title="Event", date_start=start, date_end=end, reminder_offset=600)
    session.add(event)
    session.flush()

    # remind_at after event start should fail
    future_remind = start + timedelta(minutes=1)
    with pytest.raises(ValueError):
        reminder = Reminder(user_id=1, event_id=event.id, event=event, remind_at=future_remind)
        session.add(reminder)
        session.flush()


def test_sent_default_false(session):
    start = datetime(2025, 11, 20, 12, 0, tzinfo=UTC)
    end = start + timedelta(hours=1)
    event = Event(user_id=1, title="Event", date_start=start, date_end=end, reminder_offset=600)
    session.add(event)
    session.flush()

    reminder = Reminder(user_id=1, event_id=event.id, event=event, remind_at=compute_remind_at(event))
    session.add(reminder)
    session.flush()

    assert reminder.sent is False
