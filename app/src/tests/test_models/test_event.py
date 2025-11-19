"""
Unit tests for the Event model.

Tests cover:
- ORM-level validation (ValueError)
- SQL-level constraints (IntegrityError)
- Default values
"""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.bot.database import Base
from src.bot.models.calendar import Calendar
from src.bot.models.event import Event


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


# ---------------------------------------------------------------------------
# ORM VALIDATION TESTS
# ---------------------------------------------------------------------------


def test_title_cannot_be_empty(session):
    with pytest.raises(ValueError):
        event = Event(
            user_id=1, title="   ", date_start=datetime.now(UTC), date_end=datetime.now(UTC) + timedelta(hours=1)
        )
        session.add(event)
        session.flush()


def test_title_max_length(session):
    with pytest.raises(ValueError):
        event = Event(
            user_id=1, title="a" * 256, date_start=datetime.now(UTC), date_end=datetime.now(UTC) + timedelta(hours=1)
        )
        session.add(event)
        session.flush()


def test_description_max_length(session):
    with pytest.raises(ValueError):
        event = Event(
            user_id=1,
            title="Test Event",
            description="d" * 1025,
            date_start=datetime.now(UTC),
            date_end=datetime.now(UTC) + timedelta(hours=1),
        )
        session.add(event)
        session.flush()


def test_rrule_format_invalid(session):
    with pytest.raises(ValueError):
        event = Event(
            user_id=1,
            title="Event with bad RRULE",
            rrule="INVALID=RULE",
            date_start=datetime.now(UTC),
            date_end=datetime.now(UTC) + timedelta(hours=1),
        )
        session.add(event)
        session.flush()


def test_date_end_not_before_start(session):
    start = datetime.now(UTC)
    end = start - timedelta(hours=1)
    with pytest.raises(ValueError):
        event = Event(
            user_id=1,
            title="Bad dates",
            date_start=start,
            date_end=end,
        )
        session.add(event)
        session.flush()


def test_last_modified_not_before_created(session):
    start = datetime.now(UTC)
    end = start + timedelta(hours=1)
    created = datetime.now(UTC)
    last_modified = created - timedelta(minutes=1)
    with pytest.raises(ValueError):
        event = Event(
            user_id=1,
            title="Invalid last_modified",
            date_start=start,
            date_end=end,
            created_at=created,
            last_modified=last_modified,
        )
        session.add(event)
        session.flush()


# ---------------------------------------------------------------------------
# SQL CONSTRAINT TESTS
# ---------------------------------------------------------------------------


def test_end_after_start_constraint(session):
    start = datetime.now(UTC)
    end = start
    event = Event(
        user_id=1,
        title="Boundary test",
        date_start=start,
        date_end=end,
    )
    session.add(event)
    session.flush()  # Should not raise because date_end == date_start is allowed by SQL constraint


# ---------------------------------------------------------------------------
# DEFAULT VALUE TESTS
# ---------------------------------------------------------------------------


def test_created_at_default(session):
    start = datetime.now(UTC)
    end = start + timedelta(hours=1)
    event = Event(user_id=1, title="Default created_at", date_start=start, date_end=end)
    session.add(event)
    session.flush()
    assert event.created_at.tzinfo is not None
    assert event.created_at <= datetime.now(UTC)


def test_last_modified_default(session):
    start = datetime.now(UTC)
    end = start + timedelta(hours=1)
    event = Event(user_id=1, title="Default last_modified", date_start=start, date_end=end)
    session.add(event)
    session.flush()
    assert event.last_modified.tzinfo is not None
    assert event.last_modified <= datetime.now(UTC)


# ---------------------------------------------------------------------------
# OPTIONAL FIELD TESTS
# ---------------------------------------------------------------------------


def test_rrule_can_be_null(session):
    start = datetime.now(UTC)
    end = start + timedelta(hours=1)
    event = Event(user_id=1, title="No RRULE", date_start=start, date_end=end, rrule=None)
    session.add(event)
    session.flush()
    assert event.rrule is None


def test_description_can_be_null(session):
    start = datetime.now(UTC)
    end = start + timedelta(hours=1)
    event = Event(user_id=1, title="No Description", date_start=start, date_end=end, description=None)
    session.add(event)
    session.flush()
    assert event.description is None


def test_calendar_relation(session):
    cal = Calendar(user_id=1, name="Work", url="http://example.com/calendar.ics")
    session.add(cal)
    session.flush()
    start = datetime.now(UTC)
    end = start + timedelta(hours=1)
    event = Event(user_id=1, title="Linked Event", date_start=start, date_end=end, calendar_id=cal.id)
    session.add(event)
    session.flush()
    assert event.calendar_id == cal.id
    assert event.calendar.id == cal.id
