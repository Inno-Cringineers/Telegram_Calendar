"""
Pydantic schemas for repository operations.

These schemas provide type-safe input validation for repository methods.
"""

from dataclasses import dataclass
from datetime import datetime, time

from models.calendar import Calendar
from models.event import Event
from models.reminder import Reminder
from models.settings import Settings

NOT_SET = object()

# ----------------------------------------------------------------------------
# Event schemas
# ----------------------------------------------------------------------------


@dataclass(frozen=True)
class EventCreateSchema:
    """Schema for creating a new event.

    Attributes:
        user_id: int - Telegram user ID.
        uid: str - Event unique identifier from icalendar.

        calendar_id: int - Associated calendar ID.

        date_start: datetime - Event start date and time.
        date_end: datetime - Event end date and time.
        all_day: bool - if True, the event is all day event (in DTSTART and DTEND are only dates, without times).

        need_to_remind: bool - if True, the bot will send a reminder to the user. Needed to mute reminder notifications.

        rrule: str | None - Recurrence rule.
        rdate: list[datetime] | None - Additional recurrence dates.
        exdate: list[datetime] | None - Exception dates.

        title: str | None - Event title.
        description: str | None - Event description.
    """  # noqa: E501

    user_id: int
    uid: str
    calendar_id: int
    date_start: datetime
    date_end: datetime
    all_day: bool
    need_to_remind: bool
    rrule: str | None
    rdate: list[datetime] | None
    exdate: list[datetime] | None
    title: str | None
    description: str | None


@dataclass(frozen=True)
class EventUpdateSchema:
    """Schema for updating an existing event.

    All fields are optional - only provided fields will be updated.
    Unprovided fields remain unchanged.

    Attributes:
        date_start: datetime - Event start date and time.
        date_end: datetime - Event end date and time.
        all_day: bool - If True, the event is all day event.
        need_to_remind: bool - If True, the bot will send a reminder to the user.
        rrule: str | None - Recurrence rule.
        rdate: list[datetime] | None - Additional recurrence dates.
        exdate: list[datetime] | None - Exception dates.
        title: str | None - Event title.
        description: str | None - Event description.
    """  # noqa: E501

    date_start: datetime | object = NOT_SET
    date_end: datetime | object = NOT_SET
    all_day: bool | object = NOT_SET
    need_to_remind: bool | object = NOT_SET
    rrule: str | None | object = NOT_SET
    rdate: list[datetime] | None | object = NOT_SET
    exdate: list[datetime] | None | object = NOT_SET
    title: str | None | object = NOT_SET
    description: str | None | object = NOT_SET


@dataclass(frozen=True)
class EventFilter:
    """Schema for filtering events in repository queries.

    All fields are optional - multiple filters can be combined using AND logic.
    Filters are applied inclusively (boundaries included).

    Attributes:
        uid: str - Filter by event unique identifier from icalendar.
        user_id: int - Filter by user ID.
        calendar_id: int - Filter by calendar ID.
        start_date_from: datetime - Filter events starting from this date.
        start_date_to: datetime - Filter events starting until this date.
        need_to_remind: bool - Filter by reminder requirement.
    """  # noqa: E501

    uid: str | object = NOT_SET
    user_id: int | object = NOT_SET
    calendar_id: int | object = NOT_SET
    start_date_from: datetime | object = NOT_SET
    start_date_to: datetime | object = NOT_SET
    need_to_remind: bool | object = NOT_SET


# ----------------------------------------------------------------------------
# Calendar schemas
# ----------------------------------------------------------------------------


@dataclass(frozen=True)
class CalendarCreateSchema:
    """Schema for creating a new calendar.

    Attributes:
        user_id: int - Telegram user ID.
        name: str - Calendar name.
        url: str | None - Calendar URL.
    """

    user_id: int
    name: str
    url: str | None


@dataclass(frozen=True)
class CalendarUpdateSchema:
    """Schema for updating an existing calendar.

    All fields are optional - only provided fields will be updated.
    Unprovided fields remain unchanged.

    Attributes:
        name: str - Calendar name.
        sync_enabled: bool - Whether to enable sync with the calendar.
        last_sync: datetime - Last successful sync with the calendar.
    """

    name: str | object = NOT_SET
    sync_enabled: bool | object = NOT_SET
    last_sync: datetime | object = NOT_SET


@dataclass(frozen=True)
class CalendarFilter:
    """Schema for filtering calendars in repository queries.

    All fields are optional - multiple filters can be combined using AND logic.
    Filters are applied inclusively (boundaries included).

    Attributes:
        user_id: Filter by Telegram user ID.
        name: Filter by calendar name.
        url: Filter by calendar URL.
    """

    user_id: int | object = NOT_SET
    name: str | object = NOT_SET
    url: str | None | object = NOT_SET


# ----------------------------------------------------------------------------
# Settings schemas
# ----------------------------------------------------------------------------


@dataclass(frozen=True)
class SettingsCreateSchema:
    """Schema for creating a new settings.

    Attributes:
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

    user_id: int
    timezone: str
    language: str
    quiet_hours_enabled: bool
    quiet_hours_start: time
    quiet_hours_end: time
    daily_plans_enabled: bool
    daily_plans_time: time
    default_reminder_offset: int


@dataclass(frozen=True)
class SettingsUpdateSchema:
    """Schema for updating an existing settings.

    Attributes:
        timezone: string - The timezone of the user (e.g., "UTC+2", "UTC-3", etc.).
        language: string - The language of the user (e.g., "en", "ru", etc.).
        quiet_hours_enabled: bool - Whether the quiet hours are enabled for the user.
        quiet_hours_start: time - The start time of the quiet hours for the user.
        quiet_hours_end: time - The end time of the quiet hours for the user.
        daily_plans_enabled: bool - Whether the daily plans are enabled for the user.
        daily_plans_time: time - The time for daily plans for the user.
        default_reminder_offset: int - The default seconds before start to send reminder. By default - 15 minutes.
    """  # noqa: E501

    timezone: str | object = NOT_SET
    language: str | object = NOT_SET
    quiet_hours_enabled: bool | object = NOT_SET
    quiet_hours_start: time | object = NOT_SET
    quiet_hours_end: time | object = NOT_SET
    daily_plans_time: time | object = NOT_SET
    default_reminder_offset: int | object = NOT_SET


# ----------------------------------------------------------------------------
# Reminder schemas
# ----------------------------------------------------------------------------


@dataclass(frozen=True)
class ReminderCreateSchema:
    """Schema for creating a new reminder.

    Attributes:
        event_id: int - FK to Event, not null.
        description: string | None - DESCRIPTION. RFC 5545 format. Description of the reminder. Max 1024 chars.
        trigger_offset: string - TRIGGER in RFC 5545.Sets the interval before event start to send reminder.
            shows relative time to event start. for example: -P1D - reminder will be sent 1 day before event start.
        sent: bool - Whether the reminder has been sent. Defaults to False.
    """  # noqa: E501

    event_id: int
    description: str | None
    trigger_offset: str
    sent: bool


@dataclass(frozen=True)
class ReminderUpdateSchema:
    """Schema for updating an existing reminder.

    Attributes:
        description: str | None - DESCRIPTION. RFC 5545 format. Description of the reminder. Max 1024 chars. Optional.
        trigger_offset: string - TRIGGER in RFC 5545. Sets the interval before event start to send reminder.
            shows relative time to event start. for example: -P1D - reminder will be sent 1 day before event start.
        sent: bool - Whether the reminder has been sent. Defaults to False.
    """  # noqa: E501

    description: str | None | object = NOT_SET
    trigger_offset: str | object = NOT_SET
    sent: bool | object = NOT_SET


@dataclass(frozen=True)
class ReminderFilter:
    """Schema for filtering reminders in repository queries.

    All fields are optional - multiple filters can be combined using AND logic.
    Filters are applied inclusively (boundaries included).

    Attributes:
        event_id: int - Filter by event ID.
        user_id: int - Filter by user ID.
        sent: bool - Filter by sent status.
    """

    event_id: int | object = NOT_SET
    user_id: int | object = NOT_SET
    sent: bool | object = NOT_SET


# ----------------------------------------------------------------------------
# Response schemas (for repository return values)
# ----------------------------------------------------------------------------


@dataclass(frozen=True)
class EventResponse:
    """Response schema for Event entity.

    Contains all fields from the Event model.
    """

    id: int
    user_id: int
    uid: str
    calendar_id: int
    date_start: datetime
    date_end: datetime
    all_day: bool
    need_to_remind: bool
    rrule: str | None
    rdate: list[datetime] | None
    exdate: list[datetime] | None
    title: str | None
    description: str | None

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
        )


@dataclass(frozen=True)
class CalendarResponse:
    """Response schema for Calendar entity.

    Contains all fields from the Calendar model.
    """

    id: int
    user_id: int
    name: str
    url: str | None
    sync_enabled: bool
    last_sync: datetime | None

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


@dataclass(frozen=True)
class SettingsResponse:
    """Response schema for Settings entity.

    Contains all fields from the Settings model.
    """

    id: int
    user_id: int
    timezone: str
    language: str
    quiet_hours_enabled: bool
    quiet_hours_start: time
    quiet_hours_end: time
    daily_plans_enabled: bool
    daily_plans_time: time
    default_reminder_offset: int

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
            quiet_hours_enabled=settings.quiet_hours_enabled,
            quiet_hours_start=settings.quiet_hours_start,
            quiet_hours_end=settings.quiet_hours_end,
            daily_plans_enabled=settings.daily_plans_enabled,
            daily_plans_time=settings.daily_plans_time,
            default_reminder_offset=settings.default_reminder_offset,
        )


@dataclass(frozen=True)
class ReminderResponse:
    """Response schema for Reminder entity.

    Contains all fields from the Reminder model.
    """

    id: int
    event_id: int
    description: str | None
    trigger_offset: str
    sent: bool

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
            sent=reminder.sent,
        )
