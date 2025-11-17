import calendar
from datetime import datetime

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_main_menu_inline():
    """Main menu with 4 options."""
    buttons = [
        [InlineKeyboardButton(text="⚙️ Settings", callback_data="menu_settings")],
        [InlineKeyboardButton(text="📅 Events", callback_data="menu_events")],
        [InlineKeyboardButton(text="📋 Get Daily Plan", callback_data="menu_daily_plan")],
        [InlineKeyboardButton(text="🔗 External calendars", callback_data="menu_link_calendar")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_settings_menu_inline():
    """Settings menu with 4 options."""
    buttons = [
        [InlineKeyboardButton(text="🌍 Timezone", callback_data="settings_timezone")],
        [InlineKeyboardButton(text="🇬🇧 Language", callback_data="settings_language")],
        [InlineKeyboardButton(text="🔇 Quiet Hours", callback_data="settings_quiet_hours")],
        [InlineKeyboardButton(text="⏰ Daily Plans Time", callback_data="settings_daily_plans_time")],
        [InlineKeyboardButton(text="« Back", callback_data="back_to_main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_events_menu_inline():
    """Events menu with 4 options."""
    buttons = [
        [InlineKeyboardButton(text="📥 Import", callback_data="events_import")],
        [InlineKeyboardButton(text="📤 Export", callback_data="events_export")],
        [InlineKeyboardButton(text="➕ Add", callback_data="events_create")],
        [InlineKeyboardButton(text="🔍 View", callback_data="events_view")],
        [InlineKeyboardButton(text="« Back", callback_data="back_to_main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_events_create_inline():
    """Daily plan time menu with 2 options."""
    buttons = [
        [InlineKeyboardButton(text="📅 Create by dialog", callback_data="create_new_event")],
        [InlineKeyboardButton(text="« Back", callback_data="menu_events")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_calendar_menu_inline():
    """Calendar linking menu with 3 options."""
    buttons = [
        [InlineKeyboardButton(text="📑 List of Calendars", callback_data="calendar_list")],
        [InlineKeyboardButton(text="🔗 Link a New Calendar", callback_data="calendar_new")],
        [InlineKeyboardButton(text="« Back", callback_data="back_to_main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_back_button(callback_data: str = "back_to_main"):
    """Simple back button."""
    buttons = [
        [InlineKeyboardButton(text="« Back", callback_data=callback_data)],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_language_menu_inline():
    """Language menu with 3 options."""
    buttons = [
        [InlineKeyboardButton(text="English", callback_data="en")],
        [InlineKeyboardButton(text="Русский", callback_data="ru")],
        [InlineKeyboardButton(text="« Back", callback_data="menu_settings")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_quiet_hours_menu_inline():
    """Quiet hours menu with 2 options."""
    buttons = [
        [InlineKeyboardButton(text="enter quiet hours", callback_data="set_quite_hours")],
        [InlineKeyboardButton(text="« Back", callback_data="menu_settings")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_daily_plan_time_menu_inline():
    """Daily plan time menu with 2 options."""
    buttons = [
        [InlineKeyboardButton(text="enter daily plans time", callback_data="set_daily_plan_time")],
        [InlineKeyboardButton(text="« Back", callback_data="menu_settings")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_skip_keyboard(skip_callback: str, cancel_callback: str):
    """Keyboard with skip option."""
    buttons = [
        [InlineKeyboardButton(text="❌ Cancel", callback_data=cancel_callback)],
        [InlineKeyboardButton(text="⏭ Skip", callback_data=skip_callback)],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_cancel_keyboard(cancel_callback: str):
    """Keyboard with cancel option."""
    buttons = [
        [InlineKeyboardButton(text="❌ Cancel", callback_data=cancel_callback)],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_event_confirmation_inline():
    """Inline keyboard for event confirmation."""
    buttons = [
        [
            InlineKeyboardButton(text="✅ Accept", callback_data="confirm_event"),
            InlineKeyboardButton(text="❌ Reject", callback_data="events_cancel"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_calendar(year: int | None = None, month: int | None = None) -> InlineKeyboardMarkup:
    now = datetime.now()
    year = year or now.year
    month = month or now.month
    month_name = calendar.month_name[month]

    calendar_rows = []

    # Month and Year header
    header = [
        InlineKeyboardButton(text="<<", callback_data="prev_month"),
        InlineKeyboardButton(text=f"📅  {month_name} {year}", callback_data="ignore"),
        InlineKeyboardButton(text=">>", callback_data="next_month"),
    ]
    calendar_rows.append(header)

    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
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


def get_notification_inline():
    buttons = [
        [
            InlineKeyboardButton(text="❌ delete", callback_data="delete_notification"),
            InlineKeyboardButton(text="✎ edit", callback_data="edit_notification"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
