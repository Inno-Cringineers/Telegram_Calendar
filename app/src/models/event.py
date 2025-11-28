"""
This module defines the `Event` class, which represents calendar events in the application.
"""

from datetime import UTC, datetime
from typing import Literal

from sqlalchemy import ARRAY, Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from database.database import Base
from models.calendar import Calendar

# TODO: RRULE validation
# TODO: create indexes


class Event(Base):
    """
    Represents events linked to the user in the application, according to RFC 5545.

    RFC 5545 reference: https://www.rfc-editor.org/rfc/rfc5545

    Attributes:
        --- id section ---

        id: int - Primary key.
        user_id: int - Telegram ID of the user.
        uid: str - UID, event unique identifier from icalendar. if null - then event is not imported from external calendar.

        --- foreign keys section ---

        calendar_id: int | None - FK to Calendar entity, nullable.

        --- date section ---

        date_start: datetime - DTSTART (RFC 5545), event start date and time. Not null.
        date_end: datetime - DTEND (RFC 5545), event end date and time. Not null and must be not before start.
        all_day: bool - if True, the event is all day event (in DTSTART and DTEND are only dates, without times).

        --- reminder section ---

        need_to_remind: bool - if True, the bot will send a reminder to the user. Needed to mute reminder notifications.

        --- recurrence section (RFC 5545)---

        rrule: string | None - RRULE. RFC 5545 format. Sets the main recurrence rule.
        rdate: list[datetime] | None - RDATE. RFC 5545 format. Sets the additional recurrence dates.
        exdate: list[datetime] | None - EXDATE. RFC 5545 format. Sets the exception dates.

        examples:
        (RFC 5545 format)
        RRULE: FREQ=WEEKLY;BYDAY=MO,WE,FR;COUNT=10 - event will repeat every week on Monday, Wednesday and Friday, 10 times.
        RDATE: TZID=Europe/Moscow:20251202T090000 - event will be added to the calendar on 2025-12-02 at 09:00 Moscow time.
        EXDATE: TZID=Europe/Moscow:20251127T090000 - event will be excluded from the calendar on 2025-11-27 at 09:00 Moscow time.
        (Python representation of the above examples)
        RRULE = 'FREQ=WEEKLY;BYDAY=MO,WE,FR;COUNT=10' # event will repeat every week on Monday, Wednesday and Friday, 10 times.
        RDATE = [datetime(2025, 12, 2, 9, 0, tzinfo=UTC)] # event will be added to the calendar on 2025-12-02 at 09:00 Moscow time.
        EXDATE = [datetime(2025, 11, 27, 9, 0, tzinfo=UTC)] # event will be excluded from the calendar on 2025-11-27 at 09:00 Moscow time.

        --- content section ---

        title: string - SUMMARY. RFC 5545 format. Event title, max 255 chars. Not empty.
        description: string | None - DESCRIPTION, max 1024 chars.

        --- metadata section ---

        created_at: datetime - CREATED, auto-set if not provided.
        last_modified: datetime - LAST-MODIFIED, auto-updates on change.

    """  # noqa: E501

    # --- id section ---
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    uid: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # --- foreign keys section ---
    calendar_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("calendar.id", ondelete="CASCADE"), nullable=True
    )
    calendar: Mapped[Calendar] = relationship(
        "Calendar",
        backref="events",
        cascade="all, delete",  # automaticly delete events when calendar is deleted
        passive_deletes=True,
    )

    # --- date section ---
    date_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    date_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    all_day: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # --- reminder section ---
    need_to_remind: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # --- recurrence section---
    rrule: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rdate: Mapped[list[datetime] | None] = mapped_column(ARRAY(DateTime(timezone=True)), nullable=True)
    exdate: Mapped[list[datetime] | None] = mapped_column(ARRAY(DateTime(timezone=True)), nullable=True)

    # --- content section ---
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    # --- metadata section ---
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.now(UTC))
    last_modified: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.now(UTC), onupdate=datetime.now(UTC)
    )

    # --- SQL-level constraints ---
    __table_args__ = (
        CheckConstraint("date_end >= date_start", name="end_after_start"),
        CheckConstraint("last_modified >= created_at", name="last_modified_after_created"),
        CheckConstraint("reminder_offset >= 0", name="reminder_offset_non_negative"),
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

    @validates("date_end")
    def validate_date_end(self, key: Literal["date_end"], value: datetime) -> datetime:
        if self.date_start is not None and value < self.date_start:
            raise ValueError("Event end date (DTEND) must be not before start date (DTSTART).")
        return value
