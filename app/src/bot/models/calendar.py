"""
This module defines the `Calendar` class, which represents user-linked calendars in the application.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.bot.database import Base


class Calendar(Base):
    """
    Represents calendar linked to the user in the application.

    Attributes:
        id: int - The primary key of the calendar record.
        user_id: int - The telegram ID of the user for whom the calendar are stored.
        name: string - The name of the linked calendar. Max 255 chars.
        url: string - The ICal link to the calendar.
        last_sync: time - The last successful sync with the calendar.
        sync_enabled: bool - Indicates whether the sync with the calendar is enabled.
    """  # noqa: E501

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)

    name: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)

    last_sync: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    sync_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
