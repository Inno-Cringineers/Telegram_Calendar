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
    # Arrange
    user_id = 1
    name = "   "
    url = "http://example.com/calendar.ics"

    # Act & Assert
    with pytest.raises(ValueError):
        calendar = Calendar(user_id=user_id, name=name, url=url)

        session.add(calendar)
        session.flush()


def test_name_max_length(session):
    # Arrange
    user_id = 1
    name = "a" * 256
    url = "http://example.com/calendar.ics"

    # Act & Assert
    with pytest.raises(ValueError):
        calendar = Calendar(user_id=user_id, name=name, url=url)
        session.add(calendar)
        session.flush()


def test_url_must_start_with_http(session):
    # Arrange
    user_id = 1
    name = "Work"
    url = "ftp://example.com/calendar.ics"

    # Act & Assert
    with pytest.raises(ValueError):
        calendar = Calendar(user_id=user_id, name=name, url=url)
        session.add(calendar)
        session.flush()


def test_url_must_end_with_ics(session):
    # Arrange
    user_id = 1
    name = "Work"
    url = "http://example.com/calendar.pdf"

    # Act & Assert
    with pytest.raises(ValueError):
        calendar = Calendar(user_id=user_id, name=name, url=url)
        session.add(calendar)
        session.flush()


def test_url_max_length(session):
    # Arrange
    user_id = 1
    name = "Work"
    url = "http://example.com/" + "a" * 240 + ".ics"

    # Act & Assert
    with pytest.raises(ValueError):
        calendar = Calendar(user_id=user_id, name=name, url=url)
        session.add(calendar)
        session.flush()


def test_url_cannot_be_empty(session):
    # Arrange
    user_id = 1
    name = "Work"
    url = ""

    # Act & Assert
    with pytest.raises(ValueError):
        calendar = Calendar(user_id=user_id, name=name, url=url)
        session.add(calendar)
        session.flush()


def test_with_good_data(session):
    # Arrange
    user_id = 1
    name = "Work"
    url = "http://example.com/calendar.ics"

    # Act
    calendar: Calendar = Calendar(user_id=user_id, name=name, url=url)
    session.add(calendar)
    session.flush()

    # Assert
    assert calendar.id is not None


# ---------------------------------------------------------------------------
# SQL CONSTRAINT TESTS
# ---------------------------------------------------------------------------


def test_unique_name_constraint(session):
    # Arrange
    user_id_1 = 1
    name_1 = "Work"
    url_1 = "http://example.com/calendar1.ics"
    user_id_2 = 2
    name_2 = "Work"
    url_2 = "http://example.com/calendar2.ics"

    # Act & Assert
    with pytest.raises(IntegrityError):
        calendar_1 = Calendar(user_id=user_id_1, name=name_1, url=url_1)
        calendar_2 = Calendar(user_id=user_id_2, name=name_2, url=url_2)
        session.add(calendar_1)
        session.add(calendar_2)
        session.flush()


# ---------------------------------------------------------------------------
# DEFAULT VALUE TESTS
# ---------------------------------------------------------------------------


def test_sync_enabled_default(session):
    # Arrange
    user_id = 1
    name = "Personal"
    url = "http://example.com/personal.ics"

    # Act
    calendar: Calendar = Calendar(user_id=user_id, name=name, url=url)
    session.add(calendar)
    session.flush()

    # Assert
    assert calendar.sync_enabled is True


# ---------------------------------------------------------------------------
# OPTIONAL FIELDS TESTS
# ---------------------------------------------------------------------------


def test_last_sync_can_be_null(session):
    # Arrange
    user_id = 1
    name = "Personal"
    url = "http://example.com/personal.ics"
    last_sync = None

    # Act
    calendar: Calendar = Calendar(user_id=user_id, name=name, url=url, last_sync=last_sync)
    session.add(calendar)
    session.flush()

    # Assert
    assert calendar.last_sync is None
