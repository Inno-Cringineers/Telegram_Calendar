from datetime import UTC, datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from i18n.strings import t
from keyboards.inline import (
    get_back_button,
    get_daily_plan_time_menu_inline,
    get_language_menu_inline,
    get_quiet_hours_menu_inline,
    get_settings_menu_inline,
)
from logger.logger import logger
from states.states import SettingsStates
from store.store import Store

router = Router()


def is_valid_time(time_str: str) -> bool:
    """Validate time format HH:MM.

    Args:
        time_str: Time string to validate.

    Returns:
        True if time format is valid, False otherwise.
    """
    try:
        datetime.strptime(time_str, "%H:%M")
        return True
    except ValueError:
        return False


def detect_timezone_from_time(user_time_str: str) -> str:
    """Detect timezone from user's current time.

    Compares user's local time with UTC time to determine timezone offset.
    Always uses UTC as reference point, regardless of system timezone settings.

    Args:
        user_time_str: User's current time in HH:MM format.

    Returns:
        Timezone string in format UTC+X or UTC-X.
    """
    # Parse user's time
    user_time = datetime.strptime(user_time_str, "%H:%M").time()

    # Get current UTC time (always use UTC, not local time)
    # This ensures consistent timezone detection regardless of Docker/host timezone settings
    utc_now = datetime.now(UTC)
    utc_time = utc_now.time()

    # Calculate difference in minutes
    user_minutes = user_time.hour * 60 + user_time.minute
    utc_minutes = utc_time.hour * 60 + utc_time.minute

    # Calculate offset (can be negative if user is behind UTC)
    offset_minutes = user_minutes - utc_minutes

    # Handle day wrap-around (e.g., user is 23:00, UTC is 01:00)
    if offset_minutes > 12 * 60:  # More than 12 hours ahead
        offset_minutes -= 24 * 60  # Subtract 24 hours
    elif offset_minutes < -12 * 60:  # More than 12 hours behind
        offset_minutes += 24 * 60  # Add 24 hours

    # Convert to hours (round to nearest hour)
    offset_hours = round(offset_minutes / 60)

    # Format timezone string
    if offset_hours >= 0:
        return f"UTC+{offset_hours}"
    else:
        return f"UTC{offset_hours}"  # Negative sign is already in the number


@router.callback_query(F.data == "menu_settings")
async def open_settings_menu(query: CallbackQuery, state: FSMContext, store: Store, lang: str) -> None:
    """Open settings menu."""
    user_id = query.from_user.id
    logger.info(f"User {user_id} opened settings menu")

    await state.set_state(SettingsStates.in_settings)

    if query.message and isinstance(query.message, Message):
        await query.message.edit_text(
            t("settings.title", lang=lang),
            parse_mode="HTML",
            reply_markup=get_settings_menu_inline(lang=lang),
        )


@router.callback_query(F.data == "settings_timezone", SettingsStates.in_settings)
async def settings_timezone(query: CallbackQuery, state: FSMContext, store: Store, lang: str) -> None:
    """Handle timezone setting - ask user for current time."""
    user_id = query.from_user.id
    logger.info(f"User {user_id} is editing timezone")

    await state.set_state(SettingsStates.waiting_for_time)
    await query.answer(t("settings.timezone.selected", lang=lang))

    if query.message and isinstance(query.message, Message):
        # Get current timezone from settings
        settings_service = store.SettingsService
        settings = await settings_service.get_by_user_id(user_id)
        current_timezone = settings.timezone if settings else "UTC+3"

        text = t("settings.timezone.ask_time", lang=lang, timezone=current_timezone)
        await query.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=get_back_button("menu_settings", lang=lang),
        )


@router.message(SettingsStates.waiting_for_time)
async def process_timezone_time(message: Message, state: FSMContext, store: Store, lang: str) -> None:
    """Process user's current time and set timezone automatically."""
    if message.from_user is None:
        return

    user_id = message.from_user.id

    if message.text is None:
        await message.answer(t("settings.timezone.time_format_error", lang=lang))
        return

    time_str = message.text.strip()

    if not is_valid_time(time_str):
        await message.answer(t("settings.timezone.time_format_error", lang=lang))
        return

    # Detect timezone from user's time
    detected_timezone = detect_timezone_from_time(time_str)

    logger.info(f"User {user_id} entered time {time_str}, detected timezone: {detected_timezone}")

    # Update timezone in settings
    settings_service = store.SettingsService
    await settings_service.update_by_user_id(user_id, timezone=detected_timezone)

    # Return to settings menu
    await state.set_state(SettingsStates.in_settings)

    # Confirm timezone update
    success_text = t("settings.timezone.updated", lang=lang, timezone=detected_timezone)
    await message.answer(
        success_text,
        parse_mode="HTML",
        reply_markup=get_settings_menu_inline(lang=lang),
    )


@router.callback_query(F.data == "settings_language", SettingsStates.in_settings)
async def settings_language(query: CallbackQuery, state: FSMContext, lang: str) -> None:
    """Handle language setting."""
    user_id = query.from_user.id
    logger.info(f"User {user_id} is editing language")

    await state.set_state(SettingsStates.editing_language)
    await query.answer(t("settings.language.selected", lang=lang))

    if query.message and isinstance(query.message, Message):
        text = (
            f"{t('settings.language.title', lang=lang)}\n\n"
            f"{t('settings.language.current', lang=lang)}\n\n"
            f"<i>{t('settings.language.available', lang=lang)}</i>"
        )
        await query.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=get_language_menu_inline(lang=lang),
        )


@router.callback_query(F.data == "language_en", SettingsStates.editing_language)
async def language_en(query: CallbackQuery, state: FSMContext, store: Store, lang: str) -> None:
    """Handle language change to English."""
    user_id = query.from_user.id
    logger.info(f"User {user_id} is changing language to English")

    # Update language in settings
    settings_service = store.SettingsService
    await settings_service.update_by_user_id(user_id, language="en")

    # Return to settings menu
    await state.set_state(SettingsStates.in_settings)

    # Show popup notification
    await query.answer(t("settings.language.changed", lang="en"))

    # Update message with new language
    if query.message and isinstance(query.message, Message):
        await query.message.edit_text(
            t("settings.title", lang="en"),
            parse_mode="HTML",
            reply_markup=get_settings_menu_inline(lang="en"),
        )


@router.callback_query(F.data == "language_ru", SettingsStates.editing_language)
async def language_ru(query: CallbackQuery, state: FSMContext, store: Store, lang: str) -> None:
    """Handle language change to Russian."""
    user_id = query.from_user.id
    logger.info(f"User {user_id} is changing language to Russian")

    # Update language in settings
    settings_service = store.SettingsService
    await settings_service.update_by_user_id(user_id, language="ru")

    # Return to settings menu
    await state.set_state(SettingsStates.in_settings)

    # Show popup notification
    await query.answer(t("settings.language.changed", lang="ru"))

    # Update message with new language
    if query.message and isinstance(query.message, Message):
        await query.message.edit_text(
            t("settings.title", lang="ru"),
            parse_mode="HTML",
            reply_markup=get_settings_menu_inline(lang="ru"),
        )


@router.callback_query(F.data == "settings_quiet_hours", SettingsStates.in_settings)
async def settings_quiet_hours(query: CallbackQuery, state: FSMContext, lang: str) -> None:
    """Handle quiet hours setting."""
    user_id = query.from_user.id
    logger.info(f"User {user_id} is editing quiet hours")

    await state.set_state(SettingsStates.editing_quiet_hours)
    await query.answer(t("settings.quiet_hours.selected", lang=lang))

    if query.message and isinstance(query.message, Message):
        text = (
            f"{t('settings.quiet_hours.title', lang=lang)}\n\n"
            f"{t('settings.quiet_hours.current', lang=lang)}\n\n"
            f"<i>{t('settings.quiet_hours.description', lang=lang)}</i>"
        )
        await query.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=get_quiet_hours_menu_inline(lang=lang),
        )


@router.callback_query(F.data == "settings_daily_plans_time", SettingsStates.in_settings)
async def settings_daily_plans_time(query: CallbackQuery, state: FSMContext, lang: str) -> None:
    """Handle daily plans time setting."""
    user_id = query.from_user.id
    logger.info(f"User {user_id} is editing daily plans time")

    await state.set_state(SettingsStates.editing_daily_plans_time)
    await query.answer(t("settings.daily_plans_time.selected", lang=lang))

    if query.message and isinstance(query.message, Message):
        text = (
            f"{t('settings.daily_plans_time.title', lang=lang)}\n\n"
            f"{t('settings.daily_plans_time.current', lang=lang)}\n\n"
            f"<i>{t('settings.daily_plans_time.description', lang=lang)}</i>"
        )
        await query.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=get_daily_plan_time_menu_inline(lang=lang),
        )
