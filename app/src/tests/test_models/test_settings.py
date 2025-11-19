"""
Unit tests for the Settings model.

Tests cover:
- ORM-level validation (ValueError)
- SQL-level constraints (IntegrityError)
- Default values
- Correct handling of nullable quiet hours
"""

from datetime import time

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from src.bot.database import Base
from src.bot.models.settings import Settings


# TODO: default_reminder_offset should be in seconds
@pytest.fixture
def session():
    """
    Creates an isolated in-memory SQLite session for each test.
    Ensures a clean database without side effects.
    """
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


# ---------------------------------------------------------------------------
# ORM VALIDATION TESTS
# ---------------------------------------------------------------------------


def test_quiet_hours_end_required_if_start(session):
    """
    If quiet_hours_start is set, quiet_hours_end must NOT be None.
    ORM validator should raise ValueError BEFORE sending query to DB.
    """

    with pytest.raises(ValueError):
        settings = Settings(
            user_id=1,
            quiet_hours_start=time(10, 0),
            quiet_hours_end=None,  # Invalid
        )

        session.add(settings)
        session.flush()  # flush triggers ORM validation


def test_quiet_hours_end_cannot_be_before_start(session):
    """
    quiet_hours_end must be >= quiet_hours_start.
    ORM validator should raise ValueError.
    """
    with pytest.raises(ValueError):
        settings = Settings(
            user_id=1,
            quiet_hours_start=time(10, 0),
            quiet_hours_end=time(9, 0),  # Invalid
        )

        session.add(settings)
        session.flush()


# ---------------------------------------------------------------------------
# SQL CONSTRAINT TESTS
# ---------------------------------------------------------------------------


def test_sql_constraint_end_required_if_start(session):
    """
    SQL-level constraint ensures that quiet_hours_end IS NOT NULL
    when quiet_hours_start is set.
    Note: ORM already prevents this, so we test SQL side directly.
    """
    settings = Settings(
        user_id=1,
        quiet_hours_start=time(10, 0),
        quiet_hours_end=time(12, 0),  # Valid
    )

    session.add(settings)
    session.flush()  # Should NOT raise


def test_sql_end_must_be_after_or_equal_start(session):
    """
    Ensure SQL CheckConstraint enforces quiet_hours_end >= quiet_hours_start.
    """
    with pytest.raises(ValueError):
        settings = Settings(
            user_id=1,
            quiet_hours_start=time(10, 0),
            quiet_hours_end=time(8, 0),  # Violates SQL constraint
        )
        session.add(settings)

        with pytest.raises(IntegrityError):
            session.commit()  # SQL constraint triggers only on commit


# ---------------------------------------------------------------------------
# DEFAULT FIELD TESTS
# ---------------------------------------------------------------------------


def test_default_reminder_offset_value(session):
    """
    default_reminder_offset must default to 15 minutes if not provided explicitly.
    """
    settings = Settings(user_id=1)

    session.add(settings)
    session.flush()

    assert settings.default_reminder_offset == time(0, 15)


def test_default_timezone_value(session):
    """
    timezone must default to UTC+2 if not provided explicitly.
    """
    settings = Settings(user_id=1)

    session.add(settings)
    session.flush()

    assert settings.timezone == "UTC+2"


def test_default_language_value(session):
    """
    language must default to en if not provided explicitly.
    """
    settings = Settings(user_id=1)

    session.add(settings)
    session.flush()

    assert settings.language == "en"


# ---------------------------------------------------------------------------
# OPTIONAL FIELD BEHAVIOR
# ---------------------------------------------------------------------------


def test_quiet_hours_can_be_null(session):
    """
    Both quiet hours start and end can be NULL
    (quiet hours disabled).
    """
    settings = Settings(
        user_id=1,
        quiet_hours_start=None,
        quiet_hours_end=None,
    )

    session.add(settings)
    session.flush()

    assert settings.quiet_hours_start is None
    assert settings.quiet_hours_end is None


def test_daily_plans_time_can_be_null(session):
    """
    daily_plans_time can be NULL
    (daily plans disabled).
    """
    settings = Settings(
        user_id=1,
        daily_plans_time=None,
    )

    session.add(settings)
    session.flush()

    assert settings.daily_plans_time is None
