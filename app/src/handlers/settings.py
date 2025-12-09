from datetime import time, timedelta

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from i18n.strings import t
from keyboards.inline import (
    back_button,
    daily_plans_time_accept_reject_inline,
    language_menu_inline,
    quiet_hours_accept_reject_inline,
    quiet_hours_menu_inline,
    settings_menu_inline,
)
from logger.logger import logger
from middlewares.settings_middleware import SettingsData
from repositories.schemas import SettingsUpdateSchema
from states.states import SettingsStates
from store.store import Store
from utils.handlers import (
    detect_timezone_from_local_time,
    edit_message,
    get_last_message_id,
    is_valid_time_hhmm,
)

router = Router()


# TODO: enable/disable daily plans


async def get_settings_title(settings: SettingsData) -> str:
    language = "English" if settings.lang == "en" else "Русский"
    quiet_hours = None
    if settings.quiet_hours_enabled:
        quiet_hours = f"{settings.quiet_hours_start.strftime('%H:%M')} - {settings.quiet_hours_end.strftime('%H:%M')}"
    else:
        quiet_hours = "Disabled" if settings.lang == "en" else "Отключено"

    daily_plan = None
    if settings.daily_plans_time:
        daily_plan = f"{settings.daily_plans_time.strftime('%H:%M')}"
    else:
        daily_plan = "Disabled" if settings.lang == "en" else "Отключено"

    if settings.default_reminder_enabled:
        formatted = str(timedelta(seconds=settings.default_reminder_offset))
        reminder = f"{formatted}"
    else:
        reminder = "Disabled" if settings.lang == "en" else "Отключено"

    return t(
        "settings.title",
        timezone=settings.timezone,
        language=language,
        quiet_hours=quiet_hours,
        daily_plan=daily_plan,
        reminder=reminder,
        lang=settings.lang,
    )


async def get_quiet_hours(settings: SettingsData) -> str:
    if not settings.quiet_hours_enabled:
        return "Disabled" if settings.lang == "en" else "Отключено"

    return f"{settings.quiet_hours_start.strftime('%H:%M')} - {settings.quiet_hours_end.strftime('%H:%M')}"


@router.callback_query(F.data == "menu_settings")
async def open_settings_menu(query: CallbackQuery, state: FSMContext, settings: SettingsData) -> None:
    """Open settings menu."""
    await state.set_state(SettingsStates.in_settings)

    message_id = query.message.message_id
    chat_id = query.message.chat.id
    await edit_message(
        query.bot,
        chat_id,
        message_id,
        state,
        await get_settings_title(settings),
        settings_menu_inline(lang=settings.lang),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "settings_timezone", SettingsStates.in_settings)
async def settings_timezone(query: CallbackQuery, state: FSMContext, settings: SettingsData) -> None:
    """Handle timezone setting - ask user for current time."""

    await state.set_state(SettingsStates.waiting_for_time)
    await edit_message(
        query.bot,
        query.message.chat.id,
        query.message.message_id,
        state,
        t("settings.timezone.ask_time", lang=settings.lang, timezone=settings.timezone),
        back_button("menu_settings", lang=settings.lang),
        parse_mode="HTML",
    )


@router.message(SettingsStates.waiting_for_time)
async def process_timezone_time(message: Message, state: FSMContext, store: Store, settings: SettingsData) -> None:
    """Process user's current time and set timezone automatically."""

    text = message.text

    # delete user message
    await message.delete()
    # get last bot message from state
    last_message = await get_last_message_id(state)

    if last_message is None:
        logger.error("Last message is not found", extra={"state": await state.get_data()})
        return

    if text is None:
        text = "nothing" if settings.lang == "en" else "ничего"

    # validate time format
    if not is_valid_time_hhmm(text):
        await edit_message(
            message.bot,
            message.chat.id,
            last_message,
            state,
            t(
                "settings.timezone.time_format_error",
                lang=settings.lang,
                user_input=text,
            ),
            back_button("menu_settings", lang=settings.lang),
            parse_mode="HTML",
        )
        return

    # detect timezone from user's text
    timezone = detect_timezone_from_local_time(text)

    # update timezone in settings
    settings_service = store.SettingsService
    await settings_service.update_by_user_id(message.from_user.id, data=SettingsUpdateSchema(timezone=timezone))

    # show success message
    await state.set_state(SettingsStates.in_settings)
    await edit_message(
        message.bot,
        message.chat.id,
        last_message,
        state,
        t("settings.timezone.updated", lang=settings.lang, timezone=timezone),
        back_button("menu_settings", lang=settings.lang),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "settings_language", SettingsStates.in_settings)
async def settings_language(query: CallbackQuery, state: FSMContext, settings: SettingsData) -> None:
    """Handle language setting."""

    await state.set_state(SettingsStates.editing_language)

    text = (
        f"{t('settings.language.title', lang=settings.lang)}\n\n"
        f"{t('settings.language.current', lang=settings.lang)}\n\n"
        f"<i>{t('settings.language.available', lang=settings.lang)}</i>"
    )

    await edit_message(
        query.bot,
        query.message.chat.id,
        query.message.message_id,
        state,
        text,
        language_menu_inline(lang=settings.lang),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "language_en", SettingsStates.editing_language)
async def language_en(query: CallbackQuery, state: FSMContext, store: Store) -> None:
    """Handle language change to English."""
    user_id = query.from_user.id
    # Update language in settings
    settings_service = store.SettingsService
    await settings_service.update_by_user_id(user_id, data=SettingsUpdateSchema(language="en"))

    # Return to settings menu
    await state.set_state(SettingsStates.in_settings)

    await edit_message(
        query.bot,
        query.message.chat.id,
        query.message.message_id,
        state,
        t("settings.language.changed", lang="en"),
        back_button("menu_settings", lang="en"),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "language_ru", SettingsStates.editing_language)
async def language_ru(query: CallbackQuery, state: FSMContext, store: Store) -> None:
    """Handle language change to Russian."""
    user_id = query.from_user.id
    # Update language in settings
    settings_service = store.SettingsService
    await settings_service.update_by_user_id(user_id, data=SettingsUpdateSchema(language="ru"))

    # Return to settings menu
    await state.set_state(SettingsStates.in_settings)

    await edit_message(
        query.bot,
        query.message.chat.id,
        query.message.message_id,
        state,
        t("settings.language.changed", lang="ru"),
        back_button("menu_settings", lang="ru"),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "settings_quiet_hours", SettingsStates.in_settings)
async def settings_quiet_hours(query: CallbackQuery, state: FSMContext, settings: SettingsData) -> None:
    """Handle quiet hours setting."""

    await state.set_state(SettingsStates.in_quiet_hours_menu)

    quiet_hours = await get_quiet_hours(settings)
    text = (
        f"{t('settings.quiet.hours.title', lang=settings.lang)}\n\n"
        f"{t('settings.quiet.hours.current', lang=settings.lang, quiet_hours=quiet_hours)}\n\n"
        f"<i>{t('settings.quiet.hours.description', lang=settings.lang)}</i>"
    )

    await edit_message(
        query.bot,
        query.message.chat.id,
        query.message.message_id,
        state,
        text,
        quiet_hours_menu_inline(lang=settings.lang),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "enable_disable_quiet_hours", SettingsStates.in_quiet_hours_menu)
async def enable_disable_quiet_hours(query: CallbackQuery, state: FSMContext, store: Store) -> None:
    """Handle enabling/disabling quiet hours."""
    user_id = query.from_user.id
    new_settings = await store.SettingsService.switch_quiet_hours(user_id)

    text = None
    if new_settings.quiet_hours_enabled:
        text = t("settings.quiet.hours.enabled", lang=new_settings.language)
    else:
        text = t("settings.quiet.hours.disabled", lang=new_settings.language)

    await edit_message(
        query.bot,
        query.message.chat.id,
        query.message.message_id,
        state,
        text,
        back_button("menu_settings", lang=new_settings.language),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "set_quite_hours", SettingsStates.in_quiet_hours_menu)
async def set_quite_hours(query: CallbackQuery, state: FSMContext, settings: SettingsData) -> None:
    """Handle setting quiet hours."""

    await state.set_state(SettingsStates.waiting_for_quiet_hours_start)

    text = (
        f"{t('settings.quiet.hours.title', lang=settings.lang)}\n\n"
        f"{t('settings.quiet.hours.start.enter', lang=settings.lang)}\n\n"
    )

    await edit_message(
        query.bot,
        query.message.chat.id,
        query.message.message_id,
        state,
        text,
        back_button("menu_settings", lang=settings.lang),
        parse_mode="HTML",
    )


@router.message(SettingsStates.waiting_for_quiet_hours_start)
async def process_quiet_hours_start_time(message: Message, state: FSMContext, settings: SettingsData) -> None:
    """Process user's quiet hours start time and set quiet hours."""
    quiet_hours_start_time = message.text

    await message.delete()
    last_message = await get_last_message_id(state)
    if last_message is None:
        logger.error("Last message is not found", extra={"state": await state.get_data()})
        return

    if quiet_hours_start_time is None:
        quiet_hours_start_time = "nothing" if settings.lang == "en" else "ничего"

    text = (
        f"{t('settings.quiet.hours.title', lang=settings.lang)}\n\n"
        f"{t('settings.quiet.hours.start.enter', lang=settings.lang)}\n\n"
        f"<i>{t('settings.quiet.hours.format.error', lang=settings.lang, user_input=quiet_hours_start_time)}</i>"
    )
    if not is_valid_time_hhmm(quiet_hours_start_time):
        await edit_message(
            message.bot,
            message.chat.id,
            last_message,
            state,
            text,
            back_button("menu_settings", lang=settings.lang),
            parse_mode="HTML",
        )
        return

    await state.update_data(quiet_hours_start=quiet_hours_start_time)
    await state.set_state(SettingsStates.waiting_for_quiet_hours_end)

    text = (
        f"{t('settings.quiet.hours.title', lang=settings.lang)}\n\n"
        f"{t('settings.quiet.hours.start.entered', lang=settings.lang, quiet_start=quiet_hours_start_time)}\n\n"
        f"{t('settings.quiet.hours.end.enter', lang=settings.lang)}"
    )
    await edit_message(
        message.bot,
        message.chat.id,
        last_message,
        state,
        text,
        back_button("menu_settings", lang=settings.lang),
        parse_mode="HTML",
    )


@router.message(SettingsStates.waiting_for_quiet_hours_end)
async def process_quiet_hours_end(message: Message, state: FSMContext, settings: SettingsData) -> None:
    """Process user's quiet hours end time and set quiet hours."""
    quiet_hours_end = message.text

    await message.delete()
    last_message = await get_last_message_id(state)
    if last_message is None:
        logger.error("Last message is not found", extra={"state": await state.get_data()})
        return

    if quiet_hours_end is None:
        quiet_hours_end = "nothing" if settings.lang == "en" else "ничего"

    quiet_hours_start = (await state.get_data()).get("quiet_hours_start")
    if quiet_hours_start is None:
        logger.error("Quiet hours start time is not set", extra={"state": await state.get_data()})
        return

    text = (
        f"{t('settings.quiet.hours.title', lang=settings.lang)}\n\n"
        f"{t('settings.quiet.hours.start.entered', lang=settings.lang, quiet_start=quiet_hours_start)}\n\n"
        f"{t('settings.quiet.hours.end.enter', lang=settings.lang)}\n\n"
        f"<i>{t('settings.quiet.hours.format.error', lang=settings.lang, user_input=quiet_hours_end)}</i>"
    )
    if not is_valid_time_hhmm(quiet_hours_end):
        await edit_message(
            message.bot,
            message.chat.id,
            last_message,
            state,
            text,
            back_button("menu_settings", lang=settings.lang),
            parse_mode="HTML",
        )
        return

    if quiet_hours_start == quiet_hours_end:
        text = (
            f"{t('settings.quiet.hours.title', lang=settings.lang)}\n\n"
            f"{t('settings.quiet.hours.start.entered', lang=settings.lang, quiet_start=quiet_hours_start)}\n\n"
            f"{t('settings.quiet.hours.end.enter', lang=settings.lang, quiet_end=quiet_hours_end)}\n\n"
            f"<i>{t('settings.quiet.hours.equal.error', lang=settings.lang)}</i>"
        )
        await edit_message(
            message.bot,
            message.chat.id,
            last_message,
            state,
            text,
            back_button("menu_settings", lang=settings.lang),
            parse_mode="HTML",
        )
        return

    await state.update_data(quiet_hours_end=quiet_hours_end)
    await state.set_state(SettingsStates.in_settings)
    text = (
        f"{t('settings.quiet.hours.title', lang=settings.lang)}\n\n"
        f"<i>{t('settings.quiet.hours.accept.reject', lang=settings.lang, quiet_start=quiet_hours_start, quiet_end=quiet_hours_end)}</i>"  # noqa: E501
    )
    await edit_message(
        message.bot,
        message.chat.id,
        last_message,
        state,
        text,
        quiet_hours_accept_reject_inline(lang=settings.lang),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "accept_quiet_hours", SettingsStates.in_settings)
async def accept_quiet_hours(query: CallbackQuery, state: FSMContext, store: Store, settings: SettingsData) -> None:
    """Handle accepting quiet hours."""
    user_id = query.from_user.id
    quiet_hours_start = (await state.get_data()).get("quiet_hours_start")
    quiet_hours_end = (await state.get_data()).get("quiet_hours_end")

    # format time to time object
    quiet_hours_start = time(hour=int(quiet_hours_start.split(":")[0]), minute=int(quiet_hours_start.split(":")[1]))
    quiet_hours_end = time(hour=int(quiet_hours_end.split(":")[0]), minute=int(quiet_hours_end.split(":")[1]))

    settings_service = store.SettingsService
    await settings_service.update_by_user_id(
        user_id,
        data=SettingsUpdateSchema(
            quiet_hours_enabled=True,
            quiet_hours_start=quiet_hours_start,
            quiet_hours_end=quiet_hours_end,
        ),
    )
    await state.set_state(SettingsStates.in_settings)
    await edit_message(
        query.bot,
        query.message.chat.id,
        query.message.message_id,
        state,
        t("settings.quiet.hours.accepted", lang=settings.lang),
        back_button("menu_settings", lang=settings.lang),
    )


async def get_daily_plan_time(settings: SettingsData) -> str:
    if not settings.daily_plans_enabled:
        return "Disabled" if settings.lang == "en" else "Отключено"

    return f"{settings.daily_plans_time.strftime('%H:%M')}"


@router.callback_query(F.data == "settings_daily_plans_time", SettingsStates.in_settings)
async def settings_daily_plans_time(query: CallbackQuery, state: FSMContext, settings: SettingsData) -> None:
    """Handle daily plans time setting."""
    await state.set_state(SettingsStates.editing_daily_plans_time)

    daily_plan_time = await get_daily_plan_time(settings)

    text = (
        f"{t('settings.daily.plans.time.title', lang=settings.lang)}\n\n"
        f"{t('settings.daily.plans.time.current', lang=settings.lang, daily_plan=daily_plan_time)}\n\n"
        f"{t('settings.daily.plans.time.enter', lang=settings.lang)}"
    )

    await edit_message(
        query.bot,
        query.message.chat.id,
        query.message.message_id,
        state,
        text,
        back_button("menu_settings", lang=settings.lang),
        parse_mode="HTML",
    )


@router.message(SettingsStates.editing_daily_plans_time)
async def process_daily_plans_time(message: Message, state: FSMContext, settings: SettingsData) -> None:
    """Process user's daily plans time and set daily plans time."""
    daily_plans_time = message.text

    await message.delete()
    last_message = await get_last_message_id(state)
    if last_message is None:
        logger.error("Last message is not found", extra={"state": await state.get_data()})
        return

    if daily_plans_time is None:
        daily_plans_time = "nothing" if settings.lang == "en" else "ничего"

    text = (
        f"{t('settings.daily.plans.time.title', lang=settings.lang)}\n\n"
        f"{t('settings.daily.plans.time.enter', lang=settings.lang)}\n\n"
        f"<i>{t('settings.daily.plans.time.format.error', lang=settings.lang, user_input=daily_plans_time)}</i>"
    )
    if not is_valid_time_hhmm(daily_plans_time):
        await edit_message(
            message.bot,
            message.chat.id,
            last_message,
            state,
            text,
            back_button("menu_settings", lang=settings.lang),
            parse_mode="HTML",
        )
        return

    await state.update_data(daily_plans_time=daily_plans_time)
    await state.set_state(SettingsStates.in_settings)
    text = (
        f"{t('settings.daily.plans.time.title', lang=settings.lang)}\n\n"
        f"<i>{t('settings.daily.plans.time.accept.reject', lang=settings.lang, daily_plan=daily_plans_time)}</i>"
    )
    await edit_message(
        message.bot,
        message.chat.id,
        last_message,
        state,
        text,
        daily_plans_time_accept_reject_inline(lang=settings.lang),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "accept_daily_plans_time", SettingsStates.in_settings)
async def accept_daily_plans_time(
    query: CallbackQuery, state: FSMContext, store: Store, settings: SettingsData
) -> None:
    """Handle accepting daily plans time."""
    user_id = query.from_user.id
    daily_plans_time = (await state.get_data()).get("daily_plans_time")
    # format time to time object
    daily_plans_time = time(hour=int(daily_plans_time.split(":")[0]), minute=int(daily_plans_time.split(":")[1]))
    settings_service = store.SettingsService
    await settings_service.update_by_user_id(
        user_id,
        data=SettingsUpdateSchema(daily_plans_time=daily_plans_time),
    )
    await state.set_state(SettingsStates.in_settings)
    await edit_message(
        query.bot,
        query.message.chat.id,
        query.message.message_id,
        state,
        t("settings.daily.plans.time.accepted", lang=settings.lang),
        back_button("menu_settings", lang=settings.lang),
        parse_mode="HTML",
    )
