"""
This module defines the `Settings` class, which represents user settings in the application.
"""

from datetime import time

from sqlalchemy import Boolean, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column

from database.database import Base

# TODO: Think about how timezones should be presented in system
# TODO: Specify all possible timezones (may be in enum)
# TODO: Specify all possible languages (may be in enum)
# TODO: Default values for all settings should be in config may be
# TODO: Validation


class Settings(Base):
    """
    Represents user settings in the application.

    Attributes:
        id: int - The primary key of the settings record.
        user_id: int - The telegram ID of the user for whom the settings are stored.

        timezone: string - The timezone of the user (e.g., "UTC+2", "UTC-3", etc.). default - "UTC+2".

        language: string - The language of the user (e.g., "en", "ru", etc.). default - "en".

        quiet_hours_enabled: bool - Whether the quiet hours are enabled for the user. default - False.
        quiet_hours_start: time - The start time of the quiet hours for the user. default - 00:00.
        quiet_hours_end: time - The end time of the quiet hours for the user. default - 06:00.

        daily_plans_enabled: bool - Whether the daily plans are enabled for the user. default - False.
        daily_plans_time: time - The time for daily plans for the user. default - 09:00.

        default_reminder_offset: int - The default seconds before start to send reminder. By default - 15 minutes.
    """  # noqa: E501

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)

    timezone: Mapped[str] = mapped_column(String, default="UTC+2", nullable=False)
    language: Mapped[str] = mapped_column(String, default="en", nullable=False)

    quiet_hours_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    quiet_hours_start: Mapped[time] = mapped_column(Time, nullable=False, default=time(hour=0, minute=0))
    quiet_hours_end: Mapped[time] = mapped_column(Time, nullable=False, default=time(hour=6, minute=0))

    daily_plans_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    daily_plans_time: Mapped[time] = mapped_column(Time, nullable=False, default=time(hour=9, minute=0))

    default_reminder_offset: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=15 * 60,  # 15 minutes in seconds
    )
