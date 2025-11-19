from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from keyboards.inline import (
    get_back_button,
    get_daily_plan_time_menu_inline,
    get_language_menu_inline,
    get_quiet_hours_menu_inline,
    get_settings_menu_inline,
)
from logger.logger import logger
from states.states import SettingsStates

router = Router()


@router.callback_query(F.data == "menu_settings")
async def open_settings_menu(query: CallbackQuery, state: FSMContext):
    """Open settings menu."""
    user_id = query.from_user.id
    logger.info(f"User {user_id} opened settings menu")

    await state.set_state(SettingsStates.in_settings)

    if query.message and hasattr(query.message, "edit_text"):
        await query.message.edit_text(
            "⚙️ <b>Settings</b>\n\nChoose a setting to modify:",
            parse_mode="HTML",
            reply_markup=get_settings_menu_inline(),
        )


@router.callback_query(F.data == "settings_timezone", SettingsStates.in_settings)
async def settings_timezone(query: CallbackQuery, state: FSMContext):
    """Handle timezone setting."""
    user_id = query.from_user.id
    logger.info(f"User {user_id} is editing timezone")

    await state.set_state(SettingsStates.editing_timezone)
    await query.answer("✅ Timezone setting selected")

    if query.message and hasattr(query.message, "edit_text"):
        await query.message.edit_text(
            "🌍 Timezone\n\n"
            "Current timezone: UTC+2 (Mocked)\n\n"
            "Select timezone:\n"
            "[(UTC-12:00) Baker Island](https://t.me/personal_calendar_reminder_bot?start=tz_utc-12)\n"
            "[(UTC-11:00) American Samoa](https://t.me/personal_calendar_reminder_bot?start=tz_utc-11)\n"
            "[(UTC-10:00) Hawaii, Tahiti](https://t.me/personal_calendar_reminder_bot?start=tz_utc-10)\n"
            "[(UTC-09:00) Alaska (most)](https://t.me/personal_calendar_reminder_bot?start=tz_utc-9)\n"
            "[(UTC-08:00) Pacific Time (US/Canada)](https://t.me/personal_calendar_reminder_bot?start=tz_utc-8)\n"
            "[(UTC-07:00) Mountain Time](https://t.me/personal_calendar_reminder_bot?start=tz_utc-7)\n"
            "[(UTC-06:00) Central Time](https://t.me/personal_calendar_reminder_bot?start=tz_utc-6)\n"
            "[(UTC-05:00) Eastern Time](https://t.me/personal_calendar_reminder_bot?start=tz_utc-5)\n"
            "[(UTC-04:00) Atlantic Time (Canada)](https://t.me/personal_calendar_reminder_bot?start=tz_utc-4)\n"
            "[(UTC-03:00) Buenos Aires, Brasilia](https://t.me/personal_calendar_reminder_bot?start=tz_utc-3)\n"
            "[(UTC-02:00) Mid-Atlantic](https://t.me/personal_calendar_reminder_bot?start=tz_utc-2)\n"
            "[(UTC-01:00) Azores, Cape Verde](https://t.me/personal_calendar_reminder_bot?start=tz_utc-1)\n"
            "[(UTC±00:00) London, Lisbon, Dublin](https://t.me/personal_calendar_reminder_bot?start=tz_utc-0)\n"
            "[(UTC+01:00) Berlin, Rome, Paris](https://t.me/personal_calendar_reminder_bot?start=tz_utc1)\n"
            "[(UTC+02:00) Cairo, Helsinki, Kyiv](https://t.me/personal_calendar_reminder_bot?start=tz_utc2)\n"
            "[(UTC+03:00) Moscow, Istanbul](https://t.me/personal_calendar_reminder_bot?start=tz_utc3)\n"
            "[(UTC+04:00) Dubai, Baku, Tbilisi](https://t.me/personal_calendar_reminder_bot?start=tz_utc4)\n"
            "[(UTC+05:00) Tashkent, Astana](https://t.me/personal_calendar_reminder_bot?start=tz_utc5)\n"
            "[(UTC+06:00) Dhaka](https://t.me/personal_calendar_reminder_bot?start=tz_utc6)\n"
            "[(UTC+07:00) Bangkok, Jakarta](https://t.me/personal_calendar_reminder_bot?start=tz_utc7)\n"
            "[(UTC+08:00) Beijing, Singapore](https://t.me/personal_calendar_reminder_bot?start=tz_utc8)\n"
            "[(UTC+09:00) Tokyo, Seoul, Pyongyang](https://t.me/personal_calendar_reminder_bot?start=tz_utc9)\n"
            "[(UTC+10:00) Sydney, Melbourne,](https://t.me/personal_calendar_reminder_bot?start=tz_utc10)\n"
            "[(UTC+11:00) Solomon Islands, Vanuatu](https://t.me/personal_calendar_reminder_bot?start=tz_utc11)\n"
            "[(UTC+12:00) Auckland, Fiji, Marshall](https://t.me/personal_calendar_reminder_bot?start=tz_utc12)\n"
            "[(UTC+13:00) Samoa, Tonga, Phoenix](https://t.me/personal_calendar_reminder_bot?start=tz_utc13)\n"
            "[(UTC+14:00) Line Islands (Kiribati)](https://t.me/personal_calendar_reminder_bot?start=tz_utc14)\n"
            "Feature is under development.",
            parse_mode="Markdown",
            disable_web_page_preview=True,
            reply_markup=get_back_button("menu_settings"),
        )


@router.callback_query(F.data == "settings_language", SettingsStates.in_settings)
async def settings_language(query: CallbackQuery, state: FSMContext):
    """Handle language setting."""
    user_id = query.from_user.id
    logger.info(f"User {user_id} is editing language")

    await state.set_state(SettingsStates.editing_language)
    await query.answer("✅ Language setting selected")

    if query.message and hasattr(query.message, "edit_text"):
        await query.message.edit_text(
            "🇬🇧 <b>Language</b>\n\n"
            "Current language: English (Mocked)\n\n"
            "<i>Feature is under development. Available languages: English, Русский</i>",
            parse_mode="HTML",
            reply_markup=get_language_menu_inline(),
        )


@router.callback_query(F.data == "settings_quiet_hours", SettingsStates.in_settings)
async def settings_quiet_hours(query: CallbackQuery, state: FSMContext):
    """Handle quiet hours setting."""
    user_id = query.from_user.id
    logger.info(f"User {user_id} is editing quiet hours")

    await state.set_state(SettingsStates.editing_quiet_hours)
    await query.answer("✅ Quiet hours setting selected")

    if query.message and hasattr(query.message, "edit_text"):
        await query.message.edit_text(
            "🔇 <b>Quiet Hours</b>\n\n"
            "Current quiet hours: 22:00 - 08:00 (Mocked)\n\n"
            "<i>Feature is under development. No notifications will be sent during quiet hours.</i>",
            parse_mode="HTML",
            reply_markup=get_quiet_hours_menu_inline(),
        )


@router.callback_query(F.data == "settings_daily_plans_time", SettingsStates.in_settings)
async def settings_daily_plans_time(query: CallbackQuery, state: FSMContext):
    """Handle daily plans time setting."""
    user_id = query.from_user.id
    logger.info(f"User {user_id} is editing daily plans time")

    await state.set_state(SettingsStates.editing_daily_plans_time)
    await query.answer("✅ Daily plans time setting selected")

    if query.message and hasattr(query.message, "edit_text"):
        await query.message.edit_text(
            "⏰ <b>Daily Plans Time</b>\n\n"
            "Current time: 09:00 (Mocked)\n\n"
            "<i>Feature is under development. Daily plan will be sent at this time every day.</i>",
            parse_mode="HTML",
            reply_markup=get_daily_plan_time_menu_inline(),
        )
