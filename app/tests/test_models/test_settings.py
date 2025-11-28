"""Tests for Settings model using mocks."""

from datetime import time

from models.settings import Settings


def get_correct_settings_data() -> Settings:
    return Settings(
        user_id=12345,
        timezone="UTC+2",
        language="en",
        quiet_hours=False,
        quiet_hours_start=time(hour=0, minute=0),
        quiet_hours_end=time(hour=6, minute=0),
        daily_plans_time=time(hour=9, minute=0),
        default_reminder_offset=15 * 60,  # 15 minutes
    )


def test_settings_creation_with_correct_data() -> None:
    """Test that Settings can be created with default values."""
    settings = get_correct_settings_data()

    assert settings.user_id == 12345
    assert settings.timezone == "UTC+2"
    assert settings.language == "en"
    assert settings.quiet_hours is False
    assert settings.quiet_hours_start == time(hour=0, minute=0)
    assert settings.quiet_hours_end == time(hour=6, minute=0)
    assert settings.daily_plans_time == time(hour=9, minute=0)
    assert settings.default_reminder_offset == 15 * 60  # 15 minutes
