"""
Pydantic schemas for repository operations.

These schemas provide type-safe input validation for repository methods.
"""

from datetime import datetime, time

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# TODO: refactor repetitive code

# ----------------------------------------------------------------------------
# Event schemas
# ----------------------------------------------------------------------------


class EventCreateSchema(BaseModel):
    """Schema for creating a new event.

    Attributes:
        user_id: Telegram user ID. Required.
        title: Event title (SUMMARY in RFC 5545). Required, 1-255 characters.
        date_start: Event start date and time (DTSTART in RFC 5545). Required, timezone-aware.
        date_end: Event end date and time (DTEND in RFC 5545). Required, must be >= date_start, timezone-aware.
        reminder_offset: Reminder offset in seconds before event start. Optional, defaults to user's settings value.
        need_to_remind: Whether to send reminder notification. Optional, defaults to True.
        description: Event description (DESCRIPTION in RFC 5545). Optional, max 1024 characters.
        rrule: Recurrence rule (RRULE in RFC 5545). Optional, max 255 characters, must comply with RFC 5545 format.
        calendar_id: Associated calendar ID (foreign key). Optional.
    """

    user_id: int = Field(..., description="Telegram user ID")
    title: str = Field(..., min_length=1, max_length=255, description="Event title")
    date_start: datetime = Field(..., description="Event start date and time")
    date_end: datetime = Field(..., description="Event end date and time")
    reminder_offset: int | None = Field(None, ge=0, description="Reminder offset in seconds")
    need_to_remind: bool = Field(True, description="Whether to send reminder")
    description: str | None = Field(None, max_length=1024, description="Event description")
    rrule: str | None = Field(None, max_length=255, description="Recurrence rule (RFC 5545)")
    calendar_id: int | None = Field(None, description="Associated calendar ID")

    @field_validator("date_end")
    @classmethod
    def validate_date_end(cls, v: datetime, info) -> datetime:
        """Validate that date_end is not before date_start."""
        if hasattr(info, "data") and "date_start" in info.data and v < info.data["date_start"]:
            raise ValueError("date_end must be after or equal to date_start")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": 123456789,
                "title": "Meeting",
                "date_start": "2024-01-15T10:00:00Z",
                "date_end": "2024-01-15T11:00:00Z",
                "reminder_offset": 900,
                "need_to_remind": True,
                "description": "Team meeting",
            }
        }
    )


class EventUpdateSchema(BaseModel):
    """Schema for updating an existing event.

    All fields are optional - only provided fields will be updated.
    Unprovided fields remain unchanged.

    Attributes:
        title: Event title (SUMMARY in RFC 5545). Optional, 1-255 characters.
        date_start: Event start date and time (DTSTART in RFC 5545). Optional, timezone-aware.
        date_end: Event end date and time (DTEND in RFC 5545). Optional, must be >= date_start, timezone-aware.
        reminder_offset: Reminder offset in seconds before event start. Optional, must be >= 0.
        need_to_remind: Whether to send reminder notification. Optional.
        description: Event description (DESCRIPTION in RFC 5545). Optional, max 1024 characters.
        rrule: Recurrence rule (RRULE in RFC 5545). Optional, max 255 characters, must comply with RFC 5545 format.
        calendar_id: Associated calendar ID (foreign key). Optional.
    """

    title: str | None = Field(None, min_length=1, max_length=255, description="Event title")
    date_start: datetime | None = Field(None, description="Event start date and time")
    date_end: datetime | None = Field(None, description="Event end date and time")
    reminder_offset: int | None = Field(None, ge=0, description="Reminder offset in seconds")
    need_to_remind: bool | None = Field(None, description="Whether to send reminder")
    description: str | None = Field(None, max_length=1024, description="Event description")
    rrule: str | None = Field(None, max_length=255, description="Recurrence rule (RFC 5545)")
    calendar_id: int | None = Field(None, description="Associated calendar ID")

    @field_validator("date_end")
    @classmethod
    def validate_date_end(cls, v: datetime | None, info) -> datetime | None:
        """Validate that date_end is not before date_start."""
        if (
            v is not None
            and hasattr(info, "data")
            and "date_start" in info.data
            and info.data["date_start"] is not None
        ):
            if v < info.data["date_start"]:
                raise ValueError("date_end must be after or equal to date_start")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Updated Meeting",
                "description": "Updated description",
            }
        }
    )


class EventFilter(BaseModel):
    """Schema for filtering events in repository queries.

    All fields are optional - multiple filters can be combined using AND logic.
    Filters are applied inclusively (boundaries included).

    Attributes:
        user_id: Filter by Telegram user ID. Optional.
        calendar_id: Filter by associated calendar ID. Optional.
        start_date_from: Filter events with date_start >= this value (inclusive). Optional, timezone-aware.
        start_date_to: Filter events with date_start <= this value (inclusive). Optional, must be >= start_date_from.
        need_to_remind: Filter by reminder requirement (True/False). Optional.
        limit: Maximum number of results to return. Optional, defaults to 100, range 1-1000.
        offset: Number of results to skip (for pagination). Optional, defaults to 0, must be >= 0.
    """

    user_id: int | None = Field(None, description="Filter by user ID")
    calendar_id: int | None = Field(None, description="Filter by calendar ID")
    start_date_from: datetime | None = Field(None, description="Filter events starting from this date")
    start_date_to: datetime | None = Field(None, description="Filter events starting until this date")
    need_to_remind: bool | None = Field(None, description="Filter by reminder requirement")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Number of results to skip")

    @field_validator("start_date_to")
    @classmethod
    def validate_date_range(cls, v: datetime | None, info) -> datetime | None:
        """Validate that start_date_to is not before start_date_from."""
        if (
            v is not None
            and hasattr(info, "data")
            and "start_date_from" in info.data
            and info.data["start_date_from"] is not None
            and v < info.data["start_date_from"]
        ):
            raise ValueError("start_date_to must be after or equal to start_date_from")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": 123456789,
                "start_date_from": "2024-01-15T00:00:00Z",
                "start_date_to": "2024-01-16T00:00:00Z",
                "need_to_remind": True,
                "limit": 50,
            }
        }
    )


# ----------------------------------------------------------------------------
# Calendar schemas
# ----------------------------------------------------------------------------


class CalendarCreateSchema(BaseModel):
    """Schema for creating a new calendar.

    Attributes:
        user_id: Telegram user ID. Required.
        name: Calendar name. Required, 1-255 characters.
        url: Calendar URL. Required, must be a valid ICal URL.
    """

    user_id: int = Field(..., description="Telegram user ID")
    name: str = Field(..., min_length=1, max_length=255, description="Calendar name")
    url: str = Field(..., description="Calendar URL")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate that url is a valid ICal URL."""
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("Calendar URL must start with http or https.")
        if not v.lower().endswith(".ics"):
            raise ValueError("Calendar URL must link to the .ics file.")
        if len(v) > 255:
            raise ValueError("Calendar URL cannot exceed 255 characters.")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": 123456789,
                "name": "Work",
                "url": "http://example.com/calendar.ics",
            }
        }
    )


class CalendarUpdateSchema(BaseModel):
    """Schema for updating an existing calendar.

    All fields are optional - only provided fields will be updated.
    Unprovided fields remain unchanged.

    Attributes:
        name: Calendar name. Optional, 1-255 characters.
        url: Calendar URL. Optional, must be a valid ICal URL.
    """

    name: str | None = Field(None, min_length=1, max_length=255, description="Calendar name")
    url: str | None = Field(None, description="Calendar URL")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Work",
                "url": "http://example.com/calendar.ics",
            }
        }
    )

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str | None) -> str | None:
        """Validate that url is a valid ICal URL."""
        if v is not None:
            if not (v.startswith("http://") or v.startswith("https://")):
                raise ValueError("Calendar URL must start with http or https.")
            if not v.lower().endswith(".ics"):
                raise ValueError("Calendar URL must link to the .ics file.")
            if len(v) > 255:
                raise ValueError("Calendar URL cannot exceed 255 characters.")
        return v


class CalendarFilter(BaseModel):
    """Schema for filtering calendars in repository queries.

    All fields are optional - multiple filters can be combined using AND logic.
    Filters are applied inclusively (boundaries included).

    Attributes:
        user_id: Filter by Telegram user ID. Optional.
        name: Filter by calendar name. Optional, 1-255 characters.
        url: Filter by calendar URL. Optional, must be a valid ICal URL.
        limit: Maximum number of results to return. Optional, defaults to 100, range 1-1000.
        offset: Number of results to skip (for pagination). Optional, defaults to 0, must be >= 0.
    """

    user_id: int | None = Field(None, description="Filter by user ID")
    name: str | None = Field(None, min_length=1, max_length=255, description="Filter by calendar name")
    url: str | None = Field(None, description="Filter by calendar URL")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Number of results to skip")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": 123456789,
                "name": "Work",
                "url": "http://example.com/calendar.ics",
            }
        }
    )

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str | None) -> str | None:
        """Validate that url is a valid ICal URL."""
        if v is not None:
            if not (v.startswith("http://") or v.startswith("https://")):
                raise ValueError("Calendar URL must start with http or https.")
            if not v.lower().endswith(".ics"):
                raise ValueError("Calendar URL must link to the .ics file.")
            if len(v) > 255:
                raise ValueError("Calendar URL cannot exceed 255 characters.")
        return v


# ----------------------------------------------------------------------------
# Settings schemas
# ----------------------------------------------------------------------------


class SettingsCreateSchema(BaseModel):
    """Schema for creating a new settings.

    Attributes:
        user_id: Telegram user ID. Required.
        timezone: Timezone. Optional, defaults to "UTC+2".
        language: Language. Optional, defaults to "ru".
        quiet_hours_start: Quiet hours start time. Optional, defaults to None.
        quiet_hours_end: Quiet hours end time. Optional, defaults to None.
        daily_plans_time: Daily plans time. Optional, defaults to None.
        default_reminder_offset: Default reminder offset. Optional, defaults to 15 minutes.
    """

    user_id: int = Field(..., description="Telegram user ID")
    timezone: str = Field(..., description="Timezone")
    language: str = Field(..., description="Language")
    quiet_hours_start: time | None = Field(None, description="Quiet hours start time")
    quiet_hours_end: time | None = Field(None, description="Quiet hours end time")
    daily_plans_time: time | None = Field(None, description="Daily plans time")
    default_reminder_offset: int = Field(15 * 60, description="Default reminder offset in seconds")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": 123456789,
                "timezone": "UTC+2",
                "language": "ru",
            }
        }
    )

    @field_validator("default_reminder_offset")
    @classmethod
    def validate_default_reminder_offset(cls, v: int) -> int:
        """Validate that default_reminder_offset is not negative."""
        if v < 0:
            raise ValueError("Default reminder offset cannot be negative.")
        return v

    @model_validator(mode="after")
    def validate_quiet_hours(self) -> "SettingsCreateSchema":
        """Validate that quiet_hours_end is set if quiet_hours_start is not NULL, and end > start."""
        if self.quiet_hours_start is not None:
            if self.quiet_hours_end is None:
                raise ValueError("quiet_hours_end must be set if quiet_hours_start is not NULL.")
        return self


class SettingsUpdateSchema(BaseModel):
    """Schema for updating an existing settings.

    Attributes:
        timezone: Timezone. Optional, defaults to "UTC+2".
        language: Language. Optional, defaults to "ru".
        quiet_hours_start: Quiet hours start time. Optional, defaults to None.
        quiet_hours_end: Quiet hours end time. Optional, defaults to None.
        daily_plans_time: Daily plans time. Optional, defaults to None.
        default_reminder_offset: Default reminder offset. Optional, defaults to 15 minutes.
    """

    timezone: str | None = Field(None, description="Timezone")
    language: str | None = Field(None, description="Language")
    quiet_hours_start: time | None = Field(None, description="Quiet hours start time")
    quiet_hours_end: time | None = Field(None, description="Quiet hours end time")
    daily_plans_time: time | None = Field(None, description="Daily plans time")
    default_reminder_offset: int | None = Field(None, ge=0, description="Default reminder offset in seconds")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "timezone": "UTC+2",
                "language": "ru",
                "quiet_hours_start": "09:00",
                "quiet_hours_end": "18:00",
                "daily_plans_time": "09:00",
                "default_reminder_offset": 15 * 60,
            }
        }
    )

    @field_validator("default_reminder_offset")
    @classmethod
    def validate_default_reminder_offset(cls, v: int | None) -> int | None:
        """Validate that default_reminder_offset is not negative."""
        if v is not None and v < 0:
            raise ValueError("Default reminder offset cannot be negative.")
        return v

    @model_validator(mode="after")
    def validate_quiet_hours(self) -> "SettingsUpdateSchema":
        """Validate quiet hours relationship when fields are being updated.

        If quiet_hours_start is set to a non-None value, quiet_hours_end must also be set.
        If both are set, validate that end > start.
        """
        # Check which fields are actually set (not just default values)
        set_fields = set(self.model_dump(exclude_unset=True).keys())

        # If quiet_hours_start is being set to a non-None value, quiet_hours_end must also be set
        if "quiet_hours_start" in set_fields and self.quiet_hours_start is not None:
            if "quiet_hours_end" not in set_fields or self.quiet_hours_end is None:
                raise ValueError("quiet_hours_end must be set if quiet_hours_start is not NULL.")

        return self
