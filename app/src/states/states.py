from aiogram.fsm.state import State, StatesGroup


class EventsMenuStates(StatesGroup):
    """States for events menu."""

    in_events_menu = State()
    in_events_import = State()
    in_events_export = State()
    in_events_create = State()
    in_events_view = State()


class CreateEventStates(StatesGroup):
    """States for creating a new event."""

    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_start_date = State()
    waiting_for_start_time = State()
    waiting_for_confirmation = State()


class EditEventStates(StatesGroup):
    """States for editing an event."""

    waiting_for_selection = State()
    waiting_for_new_title = State()
    waiting_for_new_date = State()


class DeleteEventStates(StatesGroup):
    """States for deleting an event."""

    waiting_for_selection = State()
    waiting_for_confirmation = State()


class SettingsStates(StatesGroup):
    """States for settings menu."""

    in_settings = State()
    editing_timezone = State()
    editing_language = State()
    editing_quiet_hours = State()
    editing_daily_plans_time = State()


class CalendarLinkingStates(StatesGroup):
    """States for calendar linking."""

    in_calendar_menu = State()
    in_calendar_list = State()
    waiting_for_calendar_link = State()


class MainMenuStates(StatesGroup):
    """States for main menu."""

    in_main_menu = State()
