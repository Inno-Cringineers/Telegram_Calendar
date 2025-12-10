"""
This module defines the `Reminder` class, which represents notifications
for events in the application.
"""

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from sqlalchemy.util.typing import Literal

from database.database import Base
from models.event import Event

# TODO: validate RFC 5545 fields
# TODO: create indexes


class Reminder(Base):
    """
    Represents reminders linked to events in the application.
    references to VALARM from RFC 5545.

    RFC 5545 reference: https://www.rfc-editor.org/rfc/rfc5545

    Attributes:
        --- id section ---

        id: int - Primary key.
        event_id: int - FK to Event, not null.

        --- trigger section ---

        trigger_offset: string - TRIGGER in RFC 5545.Sets the interval before event start to send reminder.
            shows relative time to event start. for example: -P1D - reminder will be sent 1 day before event start.
    """  # noqa: E501

    # --- id section ---
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("event.id", ondelete="CASCADE"), nullable=False)
    event: Mapped[Event] = relationship("Event", backref="reminders", passive_deletes=True)

    # --- content section ---
    description: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    # --- trigger section ---
    trigger_offset: Mapped[str] = mapped_column(String(255), nullable=False)

    # --- ORM-level validation ---
    @validates("description")
    def validate_description(self, key: Literal["description"], value: str | None) -> str | None:
        if value is not None and len(value) > 1024:
            raise ValueError("description cannot exceed 1024 characters.")
        return value
