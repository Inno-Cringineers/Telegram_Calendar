"""Inline keyboard factory functions.

This module provides factory functions for creating inline keyboards used
throughout the bot interface. All keyboards support internationalization.
"""

import calendar
from datetime import datetime

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from i18n.strings import t


def get_main_menu_inline(lang: str = "ru") -> InlineKeyboardMarkup:
    """Create main menu inline keyboard.

    Args:
        lang: Language code for button labels. Defaults to "ru".

    Returns:
        InlineKeyboardMarkup with main menu options (Settings, Events, Daily Plan, External calendars).
    """
    buttons = [
        [InlineKeyboardButton(text=t("btn.settings", lang=lang), callback_data="menu_settings")],
        [InlineKeyboardButton(text=t("btn.events", lang=lang), callback_data="menu_events")],
        [InlineKeyboardButton(text=t("btn.daily_plan", lang=lang), callback_data="menu_daily_plan")],
        [InlineKeyboardButton(text=t("btn.external_calendars", lang=lang), callback_data="menu_link_calendar")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_settings_menu_inline(lang: str = "ru") -> InlineKeyboardMarkup:
    """Create settings menu inline keyboard.

    Args:
        lang: Language code for button labels. Defaults to "ru".

    Returns:
        InlineKeyboardMarkup with settings options (Timezone, Language, Quiet Hours, Daily Plans Time).
    """
    buttons = [
        [InlineKeyboardButton(text=t("btn.timezone", lang=lang), callback_data="settings_timezone")],
        [InlineKeyboardButton(text=t("btn.language", lang=lang), callback_data="settings_language")],
        [InlineKeyboardButton(text=t("btn.quiet_hours", lang=lang), callback_data="settings_quiet_hours")],
        [InlineKeyboardButton(text=t("btn.daily_plans_time", lang=lang), callback_data="settings_daily_plans_time")],
        [InlineKeyboardButton(text=t("btn.back", lang=lang), callback_data="back_to_main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_events_menu_inline(lang: str = "ru") -> InlineKeyboardMarkup:
    """Events menu with 4 options."""
    buttons = [
        [InlineKeyboardButton(text=t("btn.import", lang=lang), callback_data="events_import")],
        [InlineKeyboardButton(text=t("btn.export", lang=lang), callback_data="events_export")],
        [InlineKeyboardButton(text=t("btn.add", lang=lang), callback_data="events_create")],
        [InlineKeyboardButton(text=t("btn.view", lang=lang), callback_data="events_view")],
        [InlineKeyboardButton(text=t("btn.back", lang=lang), callback_data="back_to_main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_events_create_inline(lang: str = "ru") -> InlineKeyboardMarkup:
    """Daily plan time menu with 2 options."""
    buttons = [
        [InlineKeyboardButton(text=t("btn.create_by_dialog", lang=lang), callback_data="create_new_event")],
        [InlineKeyboardButton(text=t("btn.back", lang=lang), callback_data="menu_events")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_calendar_menu_inline(lang: str = "ru") -> InlineKeyboardMarkup:
    """Calendar linking menu with 3 options."""
    buttons = [
        [InlineKeyboardButton(text=t("btn.calendar_list", lang=lang), callback_data="calendar_list")],
        [InlineKeyboardButton(text=t("btn.link_calendar", lang=lang), callback_data="calendar_new")],
        [InlineKeyboardButton(text=t("btn.back", lang=lang), callback_data="back_to_main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_back_button(callback_data: str = "back_to_main", lang: str = "ru") -> InlineKeyboardMarkup:
    """Create a simple back button keyboard.

    Args:
        callback_data: Callback data for the back button. Defaults to "back_to_main".
        lang: Language code for button label. Defaults to "ru".

    Returns:
        InlineKeyboardMarkup with a single back button.
    """
    buttons = [
        [InlineKeyboardButton(text=t("btn.back", lang=lang), callback_data=callback_data)],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_language_menu_inline(lang: str = "ru") -> InlineKeyboardMarkup:
    """Language menu with 3 options."""
    buttons = [
        [InlineKeyboardButton(text=t("btn.language.en", lang=lang), callback_data="en")],
        [InlineKeyboardButton(text=t("btn.language.ru", lang=lang), callback_data="ru")],
        [InlineKeyboardButton(text=t("btn.back", lang=lang), callback_data="menu_settings")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_quiet_hours_menu_inline(lang: str = "ru") -> InlineKeyboardMarkup:
    """Quiet hours menu with 2 options."""
    buttons = [
        [InlineKeyboardButton(text=t("btn.quiet_hours.enter", lang=lang), callback_data="set_quite_hours")],
        [InlineKeyboardButton(text=t("btn.back", lang=lang), callback_data="menu_settings")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_daily_plan_time_menu_inline(lang: str = "ru") -> InlineKeyboardMarkup:
    """Daily plan time menu with 2 options."""
    buttons = [
        [InlineKeyboardButton(text=t("btn.daily_plan_time.enter", lang=lang), callback_data="set_daily_plan_time")],
        [InlineKeyboardButton(text=t("btn.back", lang=lang), callback_data="menu_settings")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_skip_keyboard(skip_callback: str, cancel_callback: str, lang: str = "ru") -> InlineKeyboardMarkup:
    """Keyboard with skip option."""
    buttons = [
        [InlineKeyboardButton(text=t("btn.cancel", lang=lang), callback_data=cancel_callback)],
        [InlineKeyboardButton(text=t("btn.skip", lang=lang), callback_data=skip_callback)],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_cancel_keyboard(cancel_callback: str, lang: str = "ru") -> InlineKeyboardMarkup:
    """Keyboard with cancel option."""
    buttons = [
        [InlineKeyboardButton(text=t("btn.cancel", lang=lang), callback_data=cancel_callback)],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_event_confirmation_inline(lang: str = "ru") -> InlineKeyboardMarkup:
    """Inline keyboard for event confirmation."""
    buttons = [
        [
            InlineKeyboardButton(text=t("btn.accept", lang=lang), callback_data="confirm_event"),
            InlineKeyboardButton(text=t("btn.reject", lang=lang), callback_data="events_cancel"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_calendar(year: int | None = None, month: int | None = None, lang: str = "ru") -> InlineKeyboardMarkup:
    """Create an interactive calendar inline keyboard.

    Args:
        year: Year to display. If None, uses current year.
        month: Month to display (1-12). If None, uses current month.
        lang: Language code for weekday labels. Defaults to "ru".

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
                day_str = str(day).rjust(2, "0")
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
