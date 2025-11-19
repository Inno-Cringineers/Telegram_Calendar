"""
This module defines the `Calendar` class, which represents user-linked calendars in the application.
"""

from datetime import datetime
from typing import Literal

from database.database import Base
from sqlalchemy import Boolean, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, validates


class Calendar(Base):
    """
    Represents calendar linked to the user in the application.

    Attributes:
        id: int - The primary key of the calendar record.
        user_id: int - The telegram ID of the user for whom the calendar is stored.
        name: string - The name of the linked calendar (unique, max 255 chars).
        url: string - The ICal link to the calendar (.ics file, max 255 chars).
        last_sync: datetime - The last successful sync with the calendar.
        sync_enabled: bool - Indicates whether the sync with the calendar is enabled.
    """  # noqa: E501

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    url: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    last_sync: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    sync_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # --- SQL-level constraints ---
    __table_args__ = (
        # name must be unique
        UniqueConstraint("name", name="uq_calendar_name"),
        # url must be unique
        UniqueConstraint("url", name="uq_calendar_url"),
    )

    # --- ORM-level validation ---
    @validates("name")
    def validate_name(self, key: Literal["name"], value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Calendar name cannot be empty.")
        if len(value) > 255:
            raise ValueError("Calendar name cannot exceed 255 characters.")
        return value

    @validates("url")
    def validate_url(self, key: Literal["url"], value: str) -> str:
        value = value.strip()
        if not (value.startswith("http://") or value.startswith("https://")):
            raise ValueError("Calendar URL must start with http or https.")
        if not value.lower().endswith(".ics"):
            raise ValueError("Calendar URL must link to the .ics file.")
        if len(value) > 255:
            raise ValueError("Calendar URL cannot exceed 255 characters.")
        return value

    @validates("last_sync")
    def validate_last_sync(self, key: Literal["last_sync"], value: datetime | None) -> datetime | None:
        if value is not None and not isinstance(value, datetime):
            raise ValueError("last_sync must be a datetime object or None.")
        return value
