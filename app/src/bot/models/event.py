"""
This module defines the `Event` class, which represents calendar events in the application.
"""

import re
from datetime import UTC, datetime
from typing import Literal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from src.bot.database import Base
from src.bot.models.calendar import Calendar

# Simple regex for RRULE validation (supports basic FREQ, UNTIL, COUNT, INTERVAL)
RRULE_REGEX = re.compile(r"^(FREQ=(DAILY|WEEKLY|MONTHLY|YEARLY))(;INTERVAL=\d+)?(;COUNT=\d+)?(;UNTIL=\d{8}T\d{6}Z)?$")

# TODO: Expand RRULE
# TODO: consider created_at and last_modified with timezone


class Event(Base):
    """
    Represents events linked to the user in the application, according to RFC 5545.

    RFC 5545 reference: https://www.rfc-editor.org/rfc/rfc5545

    Attributes:
        id: int - Primary key.
        user_id: int - Telegram ID of the user.
        calendar_id: int | None - FK to Calendar, nullable.
        date_start: datetime - DTSTART, event start. Not null.
        date_end: datetime - DTEND, event end. Not null and must be not before start.
        title: string - SUMMARY, event title, max 255 chars. Not empty.
        description: string | None - DESCRIPTION, max 1024 chars.
        rrule: string | None - RRULE, recurrence rule. RFC 5545 format.
        created_at: datetime - CREATED, auto-set if not provided.
        last_modified: datetime - LAST-MODIFIED, auto-updates on change.
    """  # noqa: E501

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)

    calendar_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("calendar.id", ondelete="CASCADE"), nullable=True
    )
    calendar: Mapped[Calendar] = relationship(
        "Calendar",
        backref="events",
        cascade="all, delete",  # automaticly delete events when calendar is deleted
        passive_deletes=True,
    )

    date_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    date_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    rrule: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(), nullable=False, default=datetime.now(UTC))
    last_modified: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now(UTC), onupdate=datetime.now(UTC)
    )

    # --- SQL-level constraints ---
    __table_args__ = (
        CheckConstraint("date_end >= date_start", name="end_after_start"),
        CheckConstraint("last_modified >= created_at", name="last_modified_after_created"),
    )

    # --- ORM-level validation ---
    @validates("title")
    def validate_title(self, key: Literal["title"], value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Event title (SUMMARY) cannot be empty.")
        if len(value) > 255:
            raise ValueError("Event title (SUMMARY) cannot exceed 255 characters.")
        return value

    @validates("description")
    def validate_description(self, key: Literal["description"], value: str | None) -> str | None:
        if value is not None and len(value) > 1024:
            raise ValueError("Event description (DESCRIPTION) cannot exceed 1024 characters.")
        return value

    @validates("rrule")
    def validate_rrule(self, key: Literal["rrule"], value: str | None) -> str | None:
        if value is not None:
            value = value.strip().upper()
            if not RRULE_REGEX.match(value):
                raise ValueError("RRULE must comply with RFC 5545 format, e.g., 'FREQ=DAILY;COUNT=10;INTERVAL=2'")
        return value

    @validates("date_end")
    def validate_date_end(self, key: Literal["date_end"], value: datetime) -> datetime:
        if self.date_start is not None and value < self.date_start:
            raise ValueError("Event end date (DTEND) must be not before start date (DTSTART).")
        return value

    @validates("last_modified")
    def validate_last_modified(self, key: Literal["last_modified"], value: datetime) -> datetime:
        if self.created_at is not None and value < self.created_at:
            raise ValueError("last_modified cannot be earlier than created_at.")
        return value
