"""
This module defines the `Reminder` class, which represents notifications
for events in the application.
"""

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from sqlalchemy.util.typing import Literal

from database.database import Base
from models.event import Event

# TODO: validate RFC 5545 fields
# TODO: create indexes


class Reminder(Base):
    """
    Represents reminders linked to events in the application.
    represent VEVENT from RFC 5545.

    RFC 5545 reference: https://www.rfc-editor.org/rfc/rfc5545

    Attributes:
        --- id section ---
        id: int - Primary key.
        event_id: int - FK to Event, not null.

        --- content section ---
        description: string | None - DESCRIPTION. RFC 5545 format. Description of the reminder. Max 1024 chars.

        --- trigger section ---
        trigger_offset: string | None - TRIGGER in RFC 5545.Sets the interval before event start to send reminder.
            shows relative time to event start. for example: -P1D - reminder will be sent 1 day before event start.
            if null - then trigger_datetime must be set.
        trigger_datetime: datetime | None - TRIGGER in RFC 5545. Sets the exact datetime to send reminder.
            if null - then trigger_offset must be set.
            shows exact time to send reminder. for example: 2025-11-20T12:00:00Z - reminder will be sent at 2025-11-20T12:00:00Z.

        --- repeat section ---
        repeat_count: int | None - REPEAT in RFC 5545. Sets the number of times to repeat the reminder.
            if null - then reminder will be sent only once.
        repeat_interval: string | None - DURATION in RFC 5545. Sets the interval to repeat the reminder.
            for example: PT10M - reminder will be sent every 10 minutes.

        --- metadata section ---
        sent: bool - Whether the reminder has been sent. Defaults to False.
    """  # noqa: E501

    # --- id section ---
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("event.id", ondelete="CASCADE"), nullable=False)
    event: Mapped[Event] = relationship("Event", backref="reminders", passive_deletes=True)

    # --- content section ---
    description: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    # --- trigger section ---
    trigger_offset: Mapped[str | None] = mapped_column(String(255), nullable=True)
    trigger_datetime: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # --- repeat section ---
    repeat_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    repeat_interval: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # --- metadata section ---
    sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # --- SQL-level constraints ---
    __table_args__ = (
        # trigger_datetime is required to be not null if trigger_offset is set (trigger is set)
        CheckConstraint(
            "(trigger_offset IS NULL OR trigger_datetime IS NOT NULL)", name="trigger_datetime_required_if_offset_set"
        ),
        # trigger_offset is required to be not null if trigger_datetime is set (trigger is set)
        CheckConstraint(
            "(trigger_datetime IS NULL OR trigger_offset IS NOT NULL)", name="trigger_offset_required_if_datetime_set"
        ),
    )

    # --- ORM-level validation ---
    @validates("description")
    def validate_description(self, key: Literal["description"], value: str | None) -> str | None:
        if value is not None and len(value) > 1024:
            raise ValueError("description cannot exceed 1024 characters.")
        return value

    @validates("repeat_count")
    def validate_repeat_count(self, key: Literal["repeat_count"], value: int | None) -> int | None:
        if value is not None and value < 0:
            raise ValueError("repeat_count cannot be negative.")
        return value
