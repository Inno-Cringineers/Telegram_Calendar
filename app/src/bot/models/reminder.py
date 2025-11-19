"""
This module defines the `Reminder` class, which represents notifications
for events in the application.
"""

from datetime import datetime, timedelta
from typing import Literal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from src.bot.database import Base
from src.bot.models.event import Event

# TODO: rename offset in settings


def compute_remind_at(event: Event) -> datetime:
    """
    Computes reminder datetime based on event.start - event.reminder_offset.

    Args:
        event: Event — must have date_start and reminder_offset.

    Returns:
        datetime with timezone: remind_at value.

    Raises:
        ValueError: If reminder_offset is invalid or leads to time >= date_start.
    """
    if event.reminder_offset is None:
        raise ValueError("Event has no reminder_offset set.")

    if not isinstance(event.reminder_offset, int):
        raise ValueError("reminder_offset must be integer seconds.")

    if event.date_start.tzinfo is None:
        raise ValueError("Event date_start must be timezone-aware.")

    remind_at = event.date_start - timedelta(seconds=event.reminder_offset)

    if remind_at >= event.date_start:
        raise ValueError("remind_at must be strictly before event start.")

    return remind_at


class Reminder(Base):
    """
    Represents reminders linked to events in the application.

    Attributes:
        id: int - Primary key.
        event_id: int - FK to Event, not null.
        remind_at: datetime - Date and time when the reminder should be sent. Not null.
        you should use compute_remind_at to compute this value.
        sent: bool - Whether the reminder has been sent. Defaults to False.
    """

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("event.id", ondelete="CASCADE"), nullable=False)
    event: Mapped[Event] = relationship("Event", backref="reminders", passive_deletes=True)

    user_id: Mapped[int] = mapped_column(Integer, nullable=False)

    remind_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # --- ORM validation ---
    @validates("remind_at")
    def validate_remind_at(self, key: Literal["remind_at"], value: datetime) -> datetime:
        if not isinstance(value, datetime):
            raise ValueError("remind_at must be a datetime instance.")

        if value.tzinfo is None:
            raise ValueError("remind_at must be timezone-aware.")
        if self.event is not None:
            if value > self.event.date_start:
                raise ValueError("Reminder time must be not after the event starts.")

        return value
