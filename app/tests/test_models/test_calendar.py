"""
Unit tests for the Calendar model.

Tests cover:
- ORM-level validation (ValueError)
- SQL-level constraints (IntegrityError)
- Default values
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from database.database import Base
from models.calendar import Calendar


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


# ---------------------------------------------------------------------------
# ORM VALIDATION TESTS
# ---------------------------------------------------------------------------


def test_name_cannot_be_empty(session):
    with pytest.raises(ValueError):
        session.add(Calendar(user_id=1, name="   ", url="http://example.com/calendar.ics"))
        session.flush()


def test_name_max_length(session):
    with pytest.raises(ValueError):
        session.add(Calendar(user_id=1, name="a" * 256, url="http://example.com/calendar.ics"))
        session.flush()


def test_url_must_start_with_http(session):
    with pytest.raises(ValueError):
        session.add(Calendar(user_id=1, name="Work", url="ftp://example.com/calendar.ics"))
        session.flush()


def test_url_must_end_with_ics(session):
    with pytest.raises(ValueError):
        session.add(Calendar(user_id=1, name="Work", url="http://example.com/calendar.pdf"))
        session.flush()


def test_url_max_length(session):
    url = "http://example.com/" + "a" * 240 + ".ics"
    with pytest.raises(ValueError):
        session.add(Calendar(user_id=1, name="Work", url=url))
        session.flush()


def test_url_cannot_be_empty(session):
    with pytest.raises(ValueError):
        session.add(Calendar(user_id=1, name="Work", url=""))
        session.flush()


def test_with_good_data(session):
    cal = Calendar(user_id=1, name="Work", url="http://example.com/calendar.ics")
    session.add(cal)
    session.flush()
    assert cal.id is not None


# ---------------------------------------------------------------------------
# SQL CONSTRAINT TESTS
# ---------------------------------------------------------------------------


def test_unique_name_constraint(session):
    cal1 = Calendar(user_id=1, name="Work", url="http://example.com/calendar1.ics")
    cal2 = Calendar(user_id=2, name="Work", url="http://example.com/calendar2.ics")

    session.add_all([cal1, cal2])

    with pytest.raises(IntegrityError):
        session.flush()
        session.commit()

    session.rollback()


# ---------------------------------------------------------------------------
# DEFAULT VALUE TESTS
# ---------------------------------------------------------------------------


def test_sync_enabled_default(session):
    cal = Calendar(user_id=1, name="Personal", url="http://example.com/personal.ics")
    session.add(cal)
    session.flush()
    assert cal.sync_enabled is True


# ---------------------------------------------------------------------------
# OPTIONAL FIELDS TESTS
# ---------------------------------------------------------------------------


def test_last_sync_can_be_null(session):
    cal = Calendar(user_id=1, name="Personal", url="http://example.com/personal.ics", last_sync=None)
    session.add(cal)
    session.flush()
    assert cal.last_sync is None
