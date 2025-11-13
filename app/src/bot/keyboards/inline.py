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
        [InlineKeyboardButton(text="➕ Add", callback_data="events_add")],
        [InlineKeyboardButton(text="🔍 Search", callback_data="events_search")],
        [InlineKeyboardButton(text="« Back", callback_data="back_to_main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_calendar_menu_inline():
    """Calendar linking menu with 2 options."""
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