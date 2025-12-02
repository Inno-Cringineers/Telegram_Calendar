"""
Pydantic schemas for repository operations.

These schemas provide type-safe input validation for repository methods.
"""

from datetime import datetime, time

from pydantic import BaseModel, Field

from models.calendar import Calendar
from models.event import Event
from models.reminder import Reminder
from models.settings import Settings

# TODO: refactor repetitive code

# ----------------------------------------------------------------------------
# Event schemas
# ----------------------------------------------------------------------------


class EventCreateSchema(BaseModel):
    """Schema for creating a new event.

    Attributes:
        user_id: int - Telegram user ID. Required.
        uid: str | None - Event unique identifier from icalendar. if null - then event is not imported from external calendar.

        calendar_id: int | None - Associated calendar ID. Optional.

        date_start: datetime - Event start date and time. Required.
        date_end: datetime - Event end date and time. Required.
        all_day: bool - if True, the event is all day event (in DTSTART and DTEND are only dates, without times).

        need_to_remind: bool - if True, the bot will send a reminder to the user. Needed to mute reminder notifications.

        rrule: str | None - Recurrence rule. Optional.
        rdate: list[datetime] | None - Additional recurrence dates. Optional.
        exdate: list[datetime] | None - Exception dates. Optional.

        title: str | None - Event title. Optional.
        description: str | None - Event description. Optional.
    """  # noqa: E501

    user_id: int = Field(..., description="Telegram user ID")
    uid: str | None = Field(
        None,
        description="Event unique identifier from icalendar. if null - then event is not imported from external calendar.",  # noqa: E501
    )
    calendar_id: int | None = Field(None, description="Associated calendar ID.")
    date_start: datetime = Field(..., description="Event start date and time.")
    date_end: datetime = Field(..., description="Event end date and time.")
    all_day: bool = Field(
        False, description="If True, the event is all day event (in DTSTART and DTEND are only dates, without times)."
    )
    need_to_remind: bool = Field(
        True, description="If True, the bot will send a reminder to the user. Needed to mute reminder notifications."
    )
    rrule: str | None = Field(None, description="Recurrence rule.")
    rdate: list[datetime] | None = Field(None, description="Additional recurrence dates.")
    exdate: list[datetime] | None = Field(None, description="Exception dates.")
    title: str | None = Field(None, description="Event title.")
    description: str | None = Field(None, description="Event description.")


class EventUpdateSchema(BaseModel):
    """Schema for updating an existing event.

    All fields are optional - only provided fields will be updated.
    Unprovided fields remain unchanged.

    Attributes:
        date_start: datetime | None - Event start date and time. Optional.
        date_end: datetime | None - Event end date and time. Optional.
        all_day: bool | None - If True, the event is all day event (in DTSTART and DTEND are only dates, without times). Optional.
        need_to_remind: bool | None - If True, the bot will send a reminder to the user. Needed to mute reminder notifications. Optional.
        rrule: str | None - Recurrence rule. Optional.
        rdate: list[datetime] | None - Additional recurrence dates. Optional.
        exdate: list[datetime] | None - Exception dates. Optional.
        title: str | None - Event title. Optional.
        description: str | None - Event description. Optional.
    """  # noqa: E501

    date_start: datetime | None = Field(None, description="Event start date and time.")
    date_end: datetime | None = Field(None, description="Event end date and time.")
    all_day: bool | None = Field(
        None, description="If True, the event is all day event (in DTSTART and DTEND are only dates, without times)."
    )
    need_to_remind: bool | None = Field(
        None, description="If True, the bot will send a reminder to the user. Needed to mute reminder notifications."
    )
    rrule: str | None = Field(None, description="Recurrence rule.")
    rdate: list[datetime] | None = Field(None, description="Additional recurrence dates.")
    exdate: list[datetime] | None = Field(None, description="Exception dates.")
    title: str | None = Field(None, description="Event title.")
    description: str | None = Field(None, description="Event description.")


class EventFilter(BaseModel):
    """Schema for filtering events in repository queries.

    All fields are optional - multiple filters can be combined using AND logic.
    Filters are applied inclusively (boundaries included).

    Attributes:
        uid: str | None - Filter by event unique identifier from icalendar. if null - then event is not imported from external calendar. Optional.
        user_id: int | None - Filter by user ID. Optional.
        calendar_id: int | None - Filter by calendar ID. Optional.
        start_date_from: datetime | None - Filter events starting from this date. Optional.
        start_date_to: datetime | None - Filter events starting until this date. Optional.
        need_to_remind: bool | None - Filter by reminder requirement. Optional.
        limit: Maximum number of results to return. Optional, defaults to 100, range 1-1000.
        offset: Number of results to skip (for pagination). Optional, defaults to 0, must be >= 0.
    """  # noqa: E501

    uid: str | None = Field(
        None,
        description="Filter by event unique identifier from icalendar. if null - then event is not imported from external calendar.",  # noqa: E501
    )
    user_id: int | None = Field(None, description="Filter by user ID.")
    calendar_id: int | None = Field(None, description="Filter by calendar ID.")
    start_date_from: datetime | None = Field(None, description="Filter events starting from this date.")
    start_date_to: datetime | None = Field(None, description="Filter events starting until this date.")
    need_to_remind: bool | None = Field(None, description="Filter by reminder requirement.")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Number of results to skip")


# ----------------------------------------------------------------------------
# Calendar schemas
# ----------------------------------------------------------------------------


class CalendarCreateSchema(BaseModel):
    """Schema for creating a new calendar.

    Attributes:
        user_id: int - Telegram user ID. Required.
        name: str - Calendar name. Required.
        url: str - Calendar URL. Required.
    """

    user_id: int = Field(..., description="Telegram user ID")
    name: str = Field(..., description="Calendar name")
    url: str | None = Field(None, description="Calendar URL")


class CalendarUpdateSchema(BaseModel):
    """Schema for updating an existing calendar.

    All fields are optional - only provided fields will be updated.
    Unprovided fields remain unchanged.

    Attributes:
        name: str - Calendar name. Optional.
        url: str - Calendar URL. Optional.
        sync_enabled: bool - Whether to enable sync with the calendar. Optional.
    """

    name: str | None = Field(None, description="Calendar name")
    url: str | None = Field(None, description="Calendar URL")
    sync_enabled: bool | None = Field(None, description="Whether to enable sync with the calendar")


class CalendarFilter(BaseModel):
    """Schema for filtering calendars in repository queries.

    All fields are optional - multiple filters can be combined using AND logic.
    Filters are applied inclusively (boundaries included).

    Attributes:
        user_id: Filter by Telegram user ID. Optional.
        name: Filter by calendar name. Optional.
        url: Filter by calendar URL. Optional.
        limit: Maximum number of results to return. Optional, defaults to 100, range 1-1000.
        offset: Number of results to skip. Optional, defaults to 0, must be >= 0.
    """

    user_id: int | None = Field(None, description="Filter by user ID")
    name: str | None = Field(None, description="Filter by calendar name")
    url: str | None = Field(None, description="Filter by calendar URL")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Number of results to skip")


# ----------------------------------------------------------------------------
# Settings schemas
# ----------------------------------------------------------------------------


class SettingsCreateSchema(BaseModel):
    """Schema for creating a new settings.

    Attributes:
        user_id: int - The telegram ID of the user for whom the settings are stored.

        timezone: string - The timezone of the user (e.g., "UTC+2", "UTC-3", etc.). default - "UTC+2".

        language: string - The language of the user (e.g., "en", "ru", etc.). default - "en".

        quiet_hours: bool - Whether the quiet hours are enabled for the user. default - False.
        quiet_hours_start: time | None - The start time of the quiet hours for the user. default - 00:00.
        quiet_hours_end: time | None - The end time of the quiet hours for the user. default - 06:00.

        daily_plans_time: time | None - The time for daily plans for the user. If null - daily plans are disabled. default - 09:00.

        default_reminder_offset: int | None - The default seconds before start to send reminder. By default - 15 minutes.
            if null - default reminder offset is not set, will not be default reminders.
    """  # noqa: E501

    user_id: int = Field(..., description="Telegram user ID")
    timezone: str = Field("UTC+2", description="Timezone")
    language: str = Field("en", description="Language")
    quiet_hours: bool = Field(False, description="Whether the quiet hours are enabled for the user")
    quiet_hours_start: time | None = Field(time(hour=0, minute=0), description="Quiet hours start time")
    quiet_hours_end: time | None = Field(time(hour=6, minute=0), description="Quiet hours end time")
    daily_plans_time: time | None = Field(time(hour=9, minute=0), description="Daily plans time")
    default_reminder_offset: int | None = Field(15 * 60, description="Default reminder offset in seconds")


class SettingsUpdateSchema(BaseModel):
    """Schema for updating an existing settings.

    Attributes:
        timezone: string | None - The timezone of the user (e.g., "UTC+2", "UTC-3", etc.). Optional.
        language: string | None - The language of the user (e.g., "en", "ru", etc.). Optional.
        quiet_hours: bool | None - Whether the quiet hours are enabled for the user. Optional.
        quiet_hours_start: time | None - The start time of the quiet hours for the user. Optional.
        quiet_hours_end: time | None - The end time of the quiet hours for the user. Optional.
        daily_plans_time: time | None - The time for daily plans for the user. If null - daily plans are disabled. Optional.
        default_reminder_offset: int | None - The default seconds before start to send reminder. By default - 15 minutes.
            if null - default reminder offset is not set, will not be default reminders. Optional.
    """  # noqa: E501

    timezone: str | None = Field(None, description="Timezone")
    language: str | None = Field(None, description="Language")
    quiet_hours: bool | None = Field(None, description="Whether the quiet hours are enabled for the user")
    quiet_hours_start: time | None = Field(None, description="Quiet hours start time")
    quiet_hours_end: time | None = Field(None, description="Quiet hours end time")
    daily_plans_time: time | None = Field(None, description="Daily plans time")
    default_reminder_offset: int | None = Field(
        None,
        description="Default seconds before start to send reminder. If null - default reminder offset is not set, will not be default reminders.",  # noqa: E501
    )


# ----------------------------------------------------------------------------
# Reminder schemas
# ----------------------------------------------------------------------------


class ReminderCreateSchema(BaseModel):
    """Schema for creating a new reminder.

    Attributes:
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
    """  # noqa: E501

    event_id: int = Field(..., description="FK to Event, not null")
    description: str | None = Field(
        None, description="DESCRIPTION. RFC 5545 format. Description of the reminder. Max 1024 chars."
    )
    trigger_offset: str | None = Field(
        None, description="TRIGGER in RFC 5545. Sets the interval before event start to send reminder."
    )
    trigger_datetime: datetime | None = Field(
        None, description="TRIGGER in RFC 5545. Sets the exact datetime to send reminder."
    )
    repeat_count: int | None = Field(
        None, description="REPEAT in RFC 5545. Sets the number of times to repeat the reminder."
    )
    repeat_interval: str | None = Field(
        None, description="DURATION in RFC 5545. Sets the interval to repeat the reminder."
    )


class ReminderUpdateSchema(BaseModel):
    """Schema for updating an existing reminder.

    Attributes:
        description: str | None - DESCRIPTION. RFC 5545 format. Description of the reminder. Max 1024 chars. Optional.
        trigger_offset: string | None - TRIGGER in RFC 5545. Sets the interval before event start to send reminder.
            shows relative time to event start. for example: -P1D - reminder will be sent 1 day before event start.
            if null - then trigger_datetime must be set. Optional.
        trigger_datetime: datetime | None - TRIGGER in RFC 5545. Sets the exact datetime to send reminder.
            if null - then trigger_offset must be set.
            shows exact time to send reminder. for example: 2025-11-20T12:00:00Z - reminder will be sent at 2025-11-20T12:00:00Z. Optional.
        repeat_count: int | None - REPEAT in RFC 5545. Sets the number of times to repeat the reminder.
            if null - then reminder will be sent only once. Optional.
        repeat_interval: string | None - DURATION in RFC 5545. Sets the interval to repeat the reminder.
            for example: PT10M - reminder will be sent every 10 minutes. Optional.
    """  # noqa: E501

    description: str | None = Field(
        None, description="DESCRIPTION. RFC 5545 format. Description of the reminder. Max 1024 chars."
    )
    trigger_offset: str | None = Field(
        None, description="TRIGGER in RFC 5545. Sets the interval before event start to send reminder."
    )
    trigger_datetime: datetime | None = Field(
        None, description="TRIGGER in RFC 5545. Sets the exact datetime to send reminder."
    )
    repeat_count: int | None = Field(
        None, description="REPEAT in RFC 5545. Sets the number of times to repeat the reminder."
    )
    repeat_interval: str | None = Field(
        None, description="DURATION in RFC 5545. Sets the interval to repeat the reminder."
    )


# ----------------------------------------------------------------------------
# Response schemas (for repository return values)
# ----------------------------------------------------------------------------


class EventResponse(BaseModel):
    """Response schema for Event entity.

    Contains all fields from the Event model, including id and metadata.
    """

    id: int = Field(..., description="Primary key")
    user_id: int = Field(..., description="Telegram user ID")
    uid: str | None = Field(None, description="Event unique identifier from icalendar")
    calendar_id: int | None = Field(None, description="Associated calendar ID")
    date_start: datetime = Field(..., description="Event start date and time")
    date_end: datetime = Field(..., description="Event end date and time")
    all_day: bool = Field(..., description="If True, the event is all day event")
    need_to_remind: bool = Field(..., description="If True, the bot will send a reminder")
    rrule: str | None = Field(None, description="Recurrence rule")
    rdate: list[datetime] | None = Field(None, description="Additional recurrence dates")
    exdate: list[datetime] | None = Field(None, description="Exception dates")
    title: str | None = Field(None, description="Event title")
    description: str | None = Field(None, description="Event description")
    created_at: datetime = Field(..., description="Creation timestamp")
    last_modified: datetime = Field(..., description="Last modification timestamp")

    @classmethod
    def from_model(cls, event: Event) -> "EventResponse":
        """Create EventResponse from Event model.

        Args:
            event: Event model instance.

        Returns:
            EventResponse instance.
        """

        return cls(
            id=event.id,
            user_id=event.user_id,
            uid=event.uid,
            calendar_id=event.calendar_id,
            date_start=event.date_start,
            date_end=event.date_end,
            all_day=event.all_day,
            need_to_remind=event.need_to_remind,
            rrule=event.rrule,
            rdate=event.rdate,
            exdate=event.exdate,
            title=event.title,
            description=event.description,
            created_at=event.created_at,
            last_modified=event.last_modified,
        )


class CalendarResponse(BaseModel):
    """Response schema for Calendar entity.

    Contains all fields from the Calendar model, including id and metadata.
    """

    id: int = Field(..., description="Primary key")
    user_id: int = Field(..., description="Telegram user ID")
    name: str = Field(..., description="Calendar name")
    url: str | None = Field(None, description="Calendar URL")
    sync_enabled: bool = Field(..., description="Whether sync is enabled")
    last_sync: datetime | None = Field(None, description="Last sync timestamp")

    @classmethod
    def from_model(cls, calendar: Calendar) -> "CalendarResponse":
        """Create CalendarResponse from Calendar model.

        Args:
            calendar: Calendar model instance.

        Returns:
            CalendarResponse instance.
        """

        return cls(
            id=calendar.id,
            user_id=calendar.user_id,
            name=calendar.name,
            url=calendar.url,
            sync_enabled=calendar.sync_enabled,
            last_sync=calendar.last_sync,
        )


class SettingsResponse(BaseModel):
    """Response schema for Settings entity.

    Contains all fields from the Settings model, including id.
    """

    id: int = Field(..., description="Primary key")
    user_id: int = Field(..., description="Telegram user ID")
    timezone: str = Field(..., description="User timezone")
    language: str = Field(..., description="User language")
    quiet_hours: bool = Field(..., description="Whether quiet hours are enabled")
    quiet_hours_start: time = Field(..., description="Quiet hours start time")
    quiet_hours_end: time = Field(..., description="Quiet hours end time")
    daily_plans_time: time | None = Field(None, description="Daily plans time")
    default_reminder_offset: int | None = Field(None, description="Default reminder offset in seconds")

    @classmethod
    def from_model(cls, settings: "Settings") -> "SettingsResponse":  # type: ignore[name-defined]
        """Create SettingsResponse from Settings model.

        Args:
            settings: Settings model instance.

        Returns:
            SettingsResponse instance.
        """

        return cls(
            id=settings.id,
            user_id=settings.user_id,
            timezone=settings.timezone,
            language=settings.language,
            quiet_hours=settings.quiet_hours,
            quiet_hours_start=settings.quiet_hours_start,
            quiet_hours_end=settings.quiet_hours_end,
            daily_plans_time=settings.daily_plans_time,
            default_reminder_offset=settings.default_reminder_offset,
        )


class ReminderResponse(BaseModel):
    """Response schema for Reminder entity.

    Contains all fields from the Reminder model, including id and metadata.
    """

    id: int = Field(..., description="Primary key")
    event_id: int = Field(..., description="FK to Event")
    description: str | None = Field(None, description="Reminder description")
    trigger_offset: str | None = Field(None, description="Trigger offset in RFC 5545 format")
    trigger_datetime: datetime | None = Field(None, description="Trigger datetime")
    repeat_count: int | None = Field(None, description="Repeat count")
    repeat_interval: str | None = Field(None, description="Repeat interval in RFC 5545 format")
    sent: bool = Field(..., description="Whether the reminder has been sent")

    @classmethod
    def from_model(cls, reminder: Reminder) -> "ReminderResponse":
        """Create ReminderResponse from Reminder model.

        Args:
            reminder: Reminder model instance.

        Returns:
            ReminderResponse instance.
        """

        return cls(
            id=reminder.id,
            event_id=reminder.event_id,
            description=reminder.description,
            trigger_offset=reminder.trigger_offset,
            trigger_datetime=reminder.trigger_datetime,
            repeat_count=reminder.repeat_count,
            repeat_interval=reminder.repeat_interval,
            sent=reminder.sent,
        )
