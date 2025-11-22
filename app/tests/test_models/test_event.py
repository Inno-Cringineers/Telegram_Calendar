"""
Unit tests for the Event model.

Tests cover:
- ORM-level validation (ValueError)
- SQL-level constraints (IntegrityError)
- Default values
- need_to_remind field
- Calendar relationship
"""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from database.database import Base
from models.calendar import Calendar
from models.event import Event


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)

    # IMPORTANT: SQLite must explicitly enable FK
    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys=ON;"))

    Session = sessionmaker(bind=engine)
    return Session()


# ---------------------------------------------------------------------------
# ORM VALIDATION TESTS
# ---------------------------------------------------------------------------


def test_title_cannot_be_empty(session):
    # Arrange
    user_id = 1
    title = "   "
    date_start = datetime.now(UTC)
    date_end = datetime.now(UTC) + timedelta(hours=1)
    reminder_offset = 15 * 60

    # Act & Assert
    with pytest.raises(ValueError):
        event: Event = Event(
            user_id=user_id, title=title, date_start=date_start, date_end=date_end, reminder_offset=reminder_offset
        )
        session.add(event)
        session.flush()


def test_title_max_length(session):
    # Arrange
    user_id = 1
    title = "a" * 256
    date_start = datetime.now(UTC)
    date_end = datetime.now(UTC) + timedelta(hours=1)
    reminder_offset = 15 * 60

    # Act & Assert
    with pytest.raises(ValueError):
        event: Event = Event(
            user_id=user_id, title=title, date_start=date_start, date_end=date_end, reminder_offset=reminder_offset
        )
        session.add(event)
        session.flush()


def test_description_max_length(session):
    # Arrange
    user_id = 1
    title = "Test Event"
    description = "d" * 1025
    date_start = datetime.now(UTC)
    date_end = datetime.now(UTC) + timedelta(hours=1)
    reminder_offset = 15 * 60

    # Act & Assert
    with pytest.raises(ValueError):
        event: Event = Event(
            user_id=user_id,
            title=title,
            description=description,
            date_start=date_start,
            date_end=date_end,
            reminder_offset=reminder_offset,
        )
        session.add(event)
        session.flush()


def test_rrule_format_invalid(session):
    # Arrange
    user_id = 1
    title = "Test Event"
    rrule = "INVALID=RULE"
    date_start = datetime.now(UTC)
    date_end = datetime.now(UTC) + timedelta(hours=1)
    reminder_offset = 15 * 60

    # Act & Assert
    with pytest.raises(ValueError):
        event: Event = Event(
            user_id=user_id,
            title=title,
            rrule=rrule,
            date_start=date_start,
            date_end=date_end,
            reminder_offset=reminder_offset,
        )
        session.add(event)
        session.flush()


def test_date_end_not_before_start(session):
    # Arrange
    user_id = 1
    title = "Bad dates"
    date_start = datetime.now(UTC)
    date_end = date_start - timedelta(hours=1)
    reminder_offset = 15 * 60

    # Act & Assert
    with pytest.raises(ValueError):
        event: Event = Event(
            user_id=user_id,
            title=title,
            date_start=date_start,
            date_end=date_end,
            reminder_offset=reminder_offset,
        )
        session.add(event)
        session.flush()


def test_last_modified_not_before_created(session):
    # Arrange
    user_id = 1
    title = "Invalid last_modified"
    date_start = datetime.now(UTC)
    date_end = date_start + timedelta(hours=1)
    created_at = datetime.now(UTC)
    last_modified = created_at - timedelta(minutes=1)
    reminder_offset = 15 * 60

    # Act & Assert
    with pytest.raises(ValueError):
        event: Event = Event(
            user_id=user_id,
            title=title,
            date_start=date_start,
            date_end=date_end,
            created_at=created_at,
            last_modified=last_modified,
            reminder_offset=reminder_offset,
        )
        session.add(event)
        session.flush()


# ---------------------------------------------------------------------------
# SQL CONSTRAINT TESTS
# ---------------------------------------------------------------------------


def test_end_after_start_constraint(session):
    # Arrange
    start = datetime.now(UTC)
    end = start  # equal is OK
    event = Event(
        user_id=1,
        title="Boundary test",
        date_start=start,
        date_end=end,
        reminder_offset=15 * 60,
    )

    # Act
    session.add(event)
    session.flush()

    # Assert
    assert event.id is not None


# ---------------------------------------------------------------------------
# DEFAULT VALUE TESTS
# ---------------------------------------------------------------------------


def test_created_at_default(session):
    # Arrange
    start = datetime.now(UTC)
    end = start + timedelta(hours=1)
    event = Event(user_id=1, title="Default created_at", date_start=start, date_end=end, reminder_offset=15 * 60)

    # Act
    session.add(event)
    session.flush()

    # Assert
    assert event.created_at.tzinfo is not None


def test_last_modified_default(session):
    # Arrange
    start = datetime.now(UTC)
    end = start + timedelta(hours=1)
    event = Event(user_id=1, title="Default last_modified", date_start=start, date_end=end, reminder_offset=15 * 60)

    # Act
    session.add(event)
    session.flush()

    # Assert
    assert event.last_modified.tzinfo is not None


# ---------------------------------------------------------------------------
# need_to_remind TESTS
# ---------------------------------------------------------------------------


def test_need_to_remind_default_true(session):
    # Arrange
    start = datetime.now(UTC)
    end = start + timedelta(hours=1)

    event = Event(
        user_id=1,
        title="With default reminder flag",
        date_start=start,
        date_end=end,
        reminder_offset=15 * 60,
    )

    # Act
    session.add(event)
    session.flush()

    # Assert
    assert event.need_to_remind is True


def test_need_to_remind_can_be_false(session):
    # Arrange
    start = datetime.now(UTC)
    end = start + timedelta(hours=1)

    event = Event(
        user_id=1,
        title="Reminder disabled",
        date_start=start,
        date_end=end,
        need_to_remind=False,
        reminder_offset=15 * 60,
    )

    # Act
    session.add(event)
    session.flush()

    # Assert
    assert event.need_to_remind is False


def test_need_to_remind_cannot_be_null(session):
    # Arrange
    start = datetime.now(UTC)
    end = start + timedelta(hours=1)

    event = Event(
        user_id=1,
        title="Null reminder flag",
        date_start=start,
        date_end=end,
        need_to_remind=None,
    )

    # Act & Assert
    with pytest.raises(IntegrityError):
        session.add(event)
        session.flush()


# ---------------------------------------------------------------------------
# OPTIONAL FIELD TESTS
# ---------------------------------------------------------------------------


def test_rrule_can_be_null(session):
    # Arrange
    start = datetime.now(UTC)
    end = start + timedelta(hours=1)
    event = Event(user_id=1, title="No RRULE", date_start=start, date_end=end, rrule=None, reminder_offset=15 * 60)

    # Act
    session.add(event)
    session.flush()

    # Assert
    assert event.rrule is None


def test_description_can_be_null(session):
    # Arrange
    start = datetime.now(UTC)
    end = start + timedelta(hours=1)
    event = Event(
        user_id=1, title="No Description", date_start=start, date_end=end, description=None, reminder_offset=15 * 60
    )

    # Act
    session.add(event)
    session.flush()

    # Assert
    assert event.description is None


# ---------------------------------------------------------------------------
# RELATIONSHIP TESTS
# ---------------------------------------------------------------------------


def test_calendar_relation(session):
    # Arrange
    cal = Calendar(
        user_id=1,
        name="Work",
        url="http://example.com/calendar.ics",
    )
    session.add(cal)
    session.flush()

    start = datetime.now(UTC)
    end = start + timedelta(hours=1)

    event = Event(
        user_id=1,
        title="Linked Event",
        date_start=start,
        date_end=end,
        calendar_id=cal.id,
        reminder_offset=15 * 60,
    )

    # Act
    session.add(event)
    session.flush()

    # Assert
    assert event.calendar_id == cal.id
    assert event.calendar.id == cal.id


def test_calendar_fk_enforced(session):
    """Should fail because calendar_id refers to nonexistent calendar."""
    # Arrange
    start = datetime.now(UTC)
    end = start + timedelta(hours=1)

    event = Event(
        user_id=1,
        title="Bad FK",
        date_start=start,
        date_end=end,
        calendar_id=999,
        reminder_offset=15 * 60,
    )

    session.add(event)

    # Act & Assert
    with pytest.raises(IntegrityError):
        session.flush()
