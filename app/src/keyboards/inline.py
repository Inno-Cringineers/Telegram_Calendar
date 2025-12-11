"""Inline keyboard factory functions.

This module provides factory functions for creating inline keyboards used
throughout the bot interface. All keyboards support internationalization.
"""

import calendar
from datetime import datetime

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from i18n.strings import t


def _mk_markup(button_rows: list[list[InlineKeyboardButton]]) -> InlineKeyboardMarkup:
    """Create an inline keyboard markup from a list of button rows."""
    return InlineKeyboardMarkup(inline_keyboard=button_rows)


def back_button(callback_data: str = "back_to_main", lang: str = "en") -> InlineKeyboardMarkup:
    """Create a back button keyboard."""
    return _mk_markup([[InlineKeyboardButton(text=t("btn.back", lang=lang), callback_data=callback_data)]])


def cancel_button(callback_data: str = "cancel", lang: str = "en") -> InlineKeyboardMarkup:
    """Create a cancel button keyboard."""
    return _mk_markup([[InlineKeyboardButton(text=t("btn.cancel", lang=lang), callback_data=callback_data)]])


def main_menu_inline(lang: str = "en") -> InlineKeyboardMarkup:
    """Create main menu inline keyboard."""
    buttons = [
        [InlineKeyboardButton(text=t("btn.settings", lang=lang), callback_data="menu_settings")],
        [InlineKeyboardButton(text=t("btn.events", lang=lang), callback_data="menu_events")],
        [InlineKeyboardButton(text=t("btn.daily_plan", lang=lang), callback_data="menu_daily_plan")],
        [InlineKeyboardButton(text=t("btn.external_calendars", lang=lang), callback_data="menu_link_calendar")],
    ]
    return _mk_markup(buttons)


def settings_menu_inline(lang: str = "en") -> InlineKeyboardMarkup:
    """Create settings menu inline keyboard."""
    buttons = [
        [InlineKeyboardButton(text=t("btn.timezone", lang=lang), callback_data="settings_timezone")],
        [InlineKeyboardButton(text=t("btn.language", lang=lang), callback_data="settings_language")],
        [InlineKeyboardButton(text=t("btn.quiet_hours", lang=lang), callback_data="settings_quiet_hours")],
        [InlineKeyboardButton(text=t("btn.daily_plans_time", lang=lang), callback_data="settings_daily_plans_time")],
        [InlineKeyboardButton(text=t("btn.default_reminder", lang=lang), callback_data="settings_default_reminder")],
        [InlineKeyboardButton(text=t("btn.back", lang=lang), callback_data="back_to_main")],
    ]
    return _mk_markup(buttons)


def events_menu_inline(lang: str = "en") -> InlineKeyboardMarkup:
    """Create events menu inline keyboard."""
    buttons = [
        [InlineKeyboardButton(text=t("btn.add", lang=lang), callback_data="events_create")],
        [InlineKeyboardButton(text=t("btn.view", lang=lang), callback_data="events_view")],
        [InlineKeyboardButton(text=t("btn.import", lang=lang), callback_data="events_import")],
        [InlineKeyboardButton(text=t("btn.export", lang=lang), callback_data="events_export")],
        [InlineKeyboardButton(text=t("btn.back", lang=lang), callback_data="back_to_main")],
    ]
    return _mk_markup(buttons)


def events_create_inline(lang: str = "en") -> InlineKeyboardMarkup:
    """Create events create inline keyboard."""
    buttons = [
        [InlineKeyboardButton(text=t("btn.create_by_dialog", lang=lang), callback_data="create_new_event")],
        [InlineKeyboardButton(text=t("btn.back", lang=lang), callback_data="menu_events")],
    ]
    return _mk_markup(buttons)


def calendar_menu_inline(lang: str = "en") -> InlineKeyboardMarkup:
    """Create calendar menu inline keyboard."""
    buttons = [
        [InlineKeyboardButton(text=t("btn.calendar_list", lang=lang), callback_data="calendar_list")],
        [InlineKeyboardButton(text=t("btn.link_calendar", lang=lang), callback_data="calendar_new")],
        [InlineKeyboardButton(text=t("btn.back", lang=lang), callback_data="back_to_main")],
    ]
    return _mk_markup(buttons)


def language_menu_inline(lang: str = "ru") -> InlineKeyboardMarkup:
    """Create language menu inline keyboard."""
    buttons = [
        [InlineKeyboardButton(text=t("btn.language.en", lang=lang), callback_data="language_en")],
        [InlineKeyboardButton(text=t("btn.language.ru", lang=lang), callback_data="language_ru")],
        [InlineKeyboardButton(text=t("btn.back", lang=lang), callback_data="menu_settings")],
    ]
    return _mk_markup(buttons)


def confirm_calendar_inline(lang: str = "en") -> InlineKeyboardMarkup:
    """Create confirm calendar inline keyboard."""
    buttons = [
        [InlineKeyboardButton(text=t("btn.accept", lang=lang), callback_data="calendar_confirm")],
        [InlineKeyboardButton(text=t("btn.reject", lang=lang), callback_data="menu_link_calendar")],
    ]
    return _mk_markup(buttons)


def quiet_hours_menu_inline(lang: str = "en") -> InlineKeyboardMarkup:
    """Create quiet hours menu inline keyboard."""
    buttons = [
        [InlineKeyboardButton(text=t("btn_quiet_hours_enable", lang=lang), callback_data="enable_disable_quiet_hours")],
        [InlineKeyboardButton(text=t("btn.quiet_hours.enter", lang=lang), callback_data="set_quite_hours")],
        [InlineKeyboardButton(text=t("btn.back", lang=lang), callback_data="menu_settings")],
    ]
    return _mk_markup(buttons)


def quiet_hours_accept_reject_inline(lang: str = "en") -> InlineKeyboardMarkup:
    """Create quiet hours accept reject inline keyboard."""
    buttons = [
        [InlineKeyboardButton(text=t("btn.accept", lang=lang), callback_data="accept_quiet_hours")],
        [InlineKeyboardButton(text=t("btn.reject", lang=lang), callback_data="menu_settings")],
    ]
    return _mk_markup(buttons)


def calendar_inline(linked: bool, calendar_id: int, lang: str = "en") -> InlineKeyboardMarkup:
    """Create calendar inline keyboard."""
    link_btn = (
        InlineKeyboardButton(text=t("btn.calendar.unlink", lang=lang), callback_data=f"calendar_unlink:{calendar_id}")
        if linked
        else InlineKeyboardButton(
            text=t("btn.calendar.link", lang=lang), callback_data=f"calendar_unlink:{calendar_id}"
        )
    )

    buttons = [
        [
            InlineKeyboardButton(
                text=t("btn.calendar.delete", lang=lang), callback_data=f"calendar_delete:{calendar_id}"
            ),
            link_btn,
            InlineKeyboardButton(
                text=t("btn.calendar.rename", lang=lang), callback_data=f"calendar_rename:{calendar_id}"
            ),
        ]
    ]
    return _mk_markup(buttons)


def confirm_calendar_rename_inline(lang: str = "en") -> InlineKeyboardMarkup:
    """Create confirm calendar rename inline keyboard."""
    buttons = [
        [InlineKeyboardButton(text=t("btn.accept", lang=lang), callback_data="calendar_rename_confirm")],
        [InlineKeyboardButton(text=t("btn.reject", lang=lang), callback_data="menu_link_calendar")],
    ]
    return _mk_markup(buttons)


def daily_plan_time_menu_inline(lang: str = "ru", enabled: bool = False) -> InlineKeyboardMarkup:
    """Create daily plan time menu inline keyboard."""
    enable_text = t("btn.daily_plan.disable", lang=lang) if enabled else t("btn.daily_plan.enable", lang=lang)
    buttons = [
        [InlineKeyboardButton(text=enable_text, callback_data="enable_disable_daily_plans")],
        [InlineKeyboardButton(text=t("btn.daily_plan_time.enter", lang=lang), callback_data="set_daily_plan_time")],
        [InlineKeyboardButton(text=t("btn.back", lang=lang), callback_data="menu_settings")],
    ]
    return _mk_markup(buttons)


def daily_plans_time_accept_reject_inline(lang: str = "en") -> InlineKeyboardMarkup:
    """Create daily plans time accept reject inline keyboard."""
    buttons = [
        [InlineKeyboardButton(text=t("btn.accept", lang=lang), callback_data="accept_daily_plans_time")],
        [InlineKeyboardButton(text=t("btn.reject", lang=lang), callback_data="menu_settings")],
    ]
    return _mk_markup(buttons)


def default_reminder_menu_inline(lang: str = "en", enabled: bool = False) -> InlineKeyboardMarkup:
    """Create default reminder menu inline keyboard."""
    enable_text = (
        t("btn.default_reminder.disable", lang=lang) if enabled else t("btn.default_reminder.enable", lang=lang)
    )
    buttons = [
        [InlineKeyboardButton(text=enable_text, callback_data="enable_disable_default_reminder")],
        [
            InlineKeyboardButton(
                text=t("btn.default_reminder_time.enter", lang=lang), callback_data="set_default_reminder_time"
            )
        ],
        [InlineKeyboardButton(text=t("btn.back", lang=lang), callback_data="menu_settings")],
    ]
    return _mk_markup(buttons)


def default_reminder_time_accept_reject_inline(lang: str = "en") -> InlineKeyboardMarkup:
    """Create default reminder time accept reject inline keyboard."""
    buttons = [
        [InlineKeyboardButton(text=t("btn.accept", lang=lang), callback_data="accept_default_reminder_time")],
        [InlineKeyboardButton(text=t("btn.reject", lang=lang), callback_data="menu_settings")],
    ]
    return _mk_markup(buttons)


def skip_inline(skip_callback: str, cancel_callback: str, lang: str = "ru") -> InlineKeyboardMarkup:
    """Create skip keyboard inline keyboard."""
    buttons = [
        [InlineKeyboardButton(text=t("btn.cancel", lang=lang), callback_data=cancel_callback)],
        [InlineKeyboardButton(text=t("btn.skip", lang=lang), callback_data=skip_callback)],
    ]
    return _mk_markup(buttons)


def cancel_inline(cancel_callback: str, lang: str = "ru") -> InlineKeyboardMarkup:
    """Create cancel keyboard inline keyboard."""
    buttons = [
        [InlineKeyboardButton(text=t("btn.cancel", lang=lang), callback_data=cancel_callback)],
    ]
    return _mk_markup(buttons)


def event_confirmation_inline(lang: str = "ru") -> InlineKeyboardMarkup:
    """Create event confirmation inline keyboard."""
    buttons = [
        [
            InlineKeyboardButton(text=t("btn.accept", lang=lang), callback_data="confirm_event"),
            InlineKeyboardButton(text=t("btn.reject", lang=lang), callback_data="reject_event"),
        ]
    ]
    return _mk_markup(buttons)


def start_time_inline(cancel_callback: str, lang: str = "ru") -> InlineKeyboardMarkup:
    """Create start time input inline keyboard with all day option."""
    buttons = [
        [InlineKeyboardButton(text=t("btn.all_day", lang=lang), callback_data="event_all_day")],
        [InlineKeyboardButton(text=t("btn.cancel", lang=lang), callback_data=cancel_callback)],
    ]
    return _mk_markup(buttons)


def create_calendar(
    year: int | None = None,
    month: int | None = None,
    lang: str = "ru",
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> InlineKeyboardMarkup:
    """Create an interactive calendar inline keyboard.

    Args:
        year: Year to display. If None, uses current year.
        month: Month to display (1-12). If None, uses current month.
        lang: Language code for weekday labels. Defaults to "ru".
        start_date: Selected start date. Dates before this will be hidden.
        end_date: Selected end date.

    Returns:
        InlineKeyboardMarkup representing a calendar for the specified month and year.
    """
    now = datetime.now()
    year = year or now.year
    month = month or now.month
    month_name = calendar.month_name[month]

    calendar_rows = []

    # Month and Year header
    header = [
        InlineKeyboardButton(text=t("calendar.prev_month", lang=lang), callback_data="prev_month"),
        InlineKeyboardButton(text=f"📅  {month_name} {year}", callback_data="ignore"),
        InlineKeyboardButton(text=t("calendar.next_month", lang=lang), callback_data="next_month"),
    ]
    calendar_rows.append(header)

    days_str = t("calendar.weekdays", lang=lang)
    days = [day.strip() for day in days_str.split(",")]
    week_header = [InlineKeyboardButton(text=day, callback_data="ignore") for day in days]
    calendar_rows.append(week_header)

    month_calendar = calendar.monthcalendar(year, month)
    for week in month_calendar:
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(text=" ", callback_data="ignore"))
            else:
                day_date = datetime(year, month, day)
                # Hide dates before start_date if it's selected
                if start_date is not None and day_date.date() < start_date.date():
                    row.append(InlineKeyboardButton(text=" ", callback_data="ignore"))
                else:
                    day_str = str(day).rjust(2, "0")
                    # Mark selected dates with brackets
                    if start_date is not None and day_date.date() == start_date.date():
                        day_str = f"[{day_str}"
                    elif end_date is not None and day_date.date() == end_date.date():
                        day_str = f"{day_str}]"
                    row.append(InlineKeyboardButton(text=day_str, callback_data=f"day_{day}"))
        calendar_rows.append(row)
    cancel_row = [InlineKeyboardButton(text="❌", callback_data="menu_events")]
    calendar_rows.append(cancel_row)
    keyboard = InlineKeyboardMarkup(inline_keyboard=calendar_rows)
    return keyboard


def get_notification_inline(lang: str = "ru") -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text=t("btn.delete", lang=lang), callback_data="delete_notification"),
            InlineKeyboardButton(text=t("btn.edit", lang=lang), callback_data="edit_notification"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
