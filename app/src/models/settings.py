"""
This module defines the `Settings` class, which represents user settings in the application.
"""

from datetime import time
from typing import Literal

from sqlalchemy import CheckConstraint, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column, validates

from database.database import Base

# TODO: Think about how timezones should be presented in system
# TODO: Specify all possible timezones (may be in enum)
# TODO: Specify all possible languages (may be in enum)
# TODO: Default values for all settings should be in config


class Settings(Base):
    """
    Represents user settings in the application.

    Attributes:
        id: int - The primary key of the settings record.
        user_id: int - The telegram ID of the user for whom the settings are stored.
        timezone: string - The timezone of the user (e.g., "UTC+2", "UTC-3", etc.).
        language: string - The language of the user (e.g., "en", "ru", etc.).
        quiet_hours_start: time - The start time of the quiet hours for the user. If null - quiet hours are disabled.
        quiet_hours_end: time - The end time of the quiet hours for the user. Not null if quiet hours are enabled.
        daily_plans_time: time - The time for daily plans for the user. If null - daily plans are disabled.
        default_reminder_offset: int - The default seconds before start to send reminder. By default - 15 minutes.
    """  # noqa: E501

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)

    timezone: Mapped[str] = mapped_column(String, default="UTC+2", nullable=False)
    language: Mapped[str] = mapped_column(String, default="en", nullable=False)

    quiet_hours_start: Mapped[time | None] = mapped_column(Time, nullable=True)
    quiet_hours_end: Mapped[time | None] = mapped_column(Time, nullable=True)

    daily_plans_time: Mapped[time | None] = mapped_column(Time, nullable=True)

    default_reminder_offset: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=15 * 60,  # 15 minutes in seconds
    )

    # --- SQL-level constraints ---
    __table_args__ = (
        # quiet_hours_end is required to be not null if quiet_hours_start is set (quiet hours are enabled)
        CheckConstraint(
            "(quiet_hours_start IS NULL OR quiet_hours_end IS NOT NULL)", name="quiet_end_required_if_start_set"
        ),
        # quiet_hours_end must be greater than quiet_hours_start
        CheckConstraint(
            "(quiet_hours_start IS NULL OR quiet_hours_end > quiet_hours_start)", name="quiet_end_after_start"
        ),
    )

    # --- ORM-level validation ---
    @validates("quiet_hours_start", "quiet_hours_end")
    def validate_quiet_hours(
        self, key: Literal["quiet_hours_start", "quiet_hours_end"], value: time | None
    ) -> time | None:
        if key == "quiet_hours_start":
            if value is not None and self.quiet_hours_end is not None:
                if self.quiet_hours_end <= value:
                    raise ValueError("quiet_hours_end cannot be earlier than quiet_hours_start.")
        elif key == "quiet_hours_end":
            if self.quiet_hours_start is not None and value is not None:
                if value <= self.quiet_hours_start:
                    raise ValueError("quiet_hours_end cannot be earlier than quiet_hours_start.")
            elif self.quiet_hours_start is not None and value is None:
                raise ValueError("quiet_hours_end must be set if quiet_hours_start is not NULL.")
        return value

    @validates("default_reminder_offset")
    def validate_default_reminder_offset(self, key: Literal["default_reminder_offset"], value: int) -> int:
        if value is None:
            raise ValueError("default_reminder_offset cannot be NULL.")

        if not isinstance(value, int):
            raise ValueError("default_reminder_offset must be an integer (seconds).")

        if value < 0:
            raise ValueError("default_reminder_offset must be non-negative.")

        return value
