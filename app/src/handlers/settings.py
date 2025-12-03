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
from states.states import SettingsStates
from store.store import Store
from utils.handlers import (
    detect_timezone_from_local_time,
    edit_message,
    get_last_message,
    is_valid_time_hhmm,
    log_action,
)

router = Router()


async def get_settings_title(user_id: int, store: Store, lang: str) -> str:
    settings = await store.SettingsService.get_by_user_id(user_id)
    if settings is None:
        return t("settings.title", lang=lang)

    language = "English" if settings.language == "en" else "Русский"
    quiet_hours = None
    if settings.quiet_hours:
        quiet_hours = f"{settings.quiet_hours_start.strftime('%H:%M')} - {settings.quiet_hours_end.strftime('%H:%M')}"
    else:
        quiet_hours = "Disabled" if lang == "en" else "Отключено"

    daily_plan = None
    if settings.daily_plans_time:
        daily_plan = f"{settings.daily_plans_time.strftime('%H:%M')}"
    else:
        daily_plan = "Disabled" if lang == "en" else "Отключено"

    return t(
        "settings.title",
        timezone=settings.timezone,
        language=language,
        quiet_hours=quiet_hours,
        daily_plan=daily_plan,
        lang=lang,
    )


async def get_quiet_hours(user_id: int, store: Store, lang: str) -> str:
    settings = await store.SettingsService.get_by_user_id(user_id)
    if settings is None or not settings.quiet_hours:
        return "Disabled" if lang == "en" else "Отключено"

    return f"{settings.quiet_hours_start.strftime('%H:%M')} - {settings.quiet_hours_end.strftime('%H:%M')}"


@router.callback_query(F.data == "menu_settings")
@log_action("User opened settings menu")
async def open_settings_menu(query: CallbackQuery, state: FSMContext, store: Store, lang: str, **kwargs) -> None:
    """Open settings menu."""
    await state.set_state(SettingsStates.in_settings)
    if query.message and isinstance(query.message, Message):
        await edit_message(
            query.message,
            state,
            await get_settings_title(query.from_user.id, store, lang),
            settings_menu_inline(lang=lang),
            parse_mode="HTML",
        )


@router.callback_query(F.data == "settings_timezone", SettingsStates.in_settings)
@log_action("User is editing timezone")
async def settings_timezone(
    query: CallbackQuery, state: FSMContext, store: Store, lang: str, timezone: str, **kwargs
) -> None:
    """Handle timezone setting - ask user for current time."""
    if query.message is None or not isinstance(query.message, Message):
        logger.error("Query message is None or not a Message", extra={"query": query})
        return
    await state.set_state(SettingsStates.waiting_for_time)
    await edit_message(
        query.message,
        state,
        t("settings.timezone.ask_time", lang=lang, timezone=timezone),
        back_button("menu_settings", lang=lang),
        parse_mode="HTML",
    )


@router.message(SettingsStates.waiting_for_time)
async def process_timezone_time(message: Message, state: FSMContext, store: Store, lang: str) -> None:
    """Process user's current time and set timezone automatically."""
    if message.from_user is None:
        return

    text = message.text

    # delete user message
    await message.delete()
    # get last bot message from state
    last_message = await get_last_message(state)

    if text is None:
        text = "nothing" if lang == "en" else "ничего"

    # validate time format
    if not is_valid_time_hhmm(text):
        await edit_message(
            last_message,
            state,
            t(
                "settings.timezone.time_format_error",
                lang=lang,
                user_input=text,
            ),
            back_button("menu_settings", lang=lang),
            parse_mode="HTML",
        )
        return

    # detect timezone from user's text
    timezone = detect_timezone_from_local_time(text)

    # update timezone in settings
    settings_service = store.SettingsService
    await settings_service.update_by_user_id(message.from_user.id, timezone=timezone)

    # show success message
    await state.set_state(SettingsStates.in_settings)
    await edit_message(
        last_message,
        state,
        t("settings.timezone.updated", lang=lang, timezone=timezone),
        back_button("menu_settings", lang=lang),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "settings_language", SettingsStates.in_settings)
@log_action("User is editing language")
async def settings_language(query: CallbackQuery, state: FSMContext, lang: str, **kwargs) -> None:
    """Handle language setting."""

    await state.set_state(SettingsStates.editing_language)

    text = (
        f"{t('settings.language.title', lang=lang)}\n\n"
        f"{t('settings.language.current', lang=lang)}\n\n"
        f"<i>{t('settings.language.available', lang=lang)}</i>"
    )

    if query.message is None or not isinstance(query.message, Message):
        logger.error("Query message is None or not a Message", extra={"query": query})
        return

    await edit_message(
        query.message,
        state,
        text,
        language_menu_inline(lang=lang),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "language_en", SettingsStates.editing_language)
async def language_en(query: CallbackQuery, state: FSMContext, store: Store, lang: str) -> None:
    """Handle language change to English."""
    user_id = query.from_user.id
    # Update language in settings
    settings_service = store.SettingsService
    await settings_service.update_by_user_id(user_id, language="en")

    # Return to settings menu
    await state.set_state(SettingsStates.in_settings)

    if query.message is None or not isinstance(query.message, Message):
        logger.error("Query message is None or not a Message", extra={"query": query})
        return

    await edit_message(
        query.message,
        state,
        t("settings.language.changed", lang="en"),
        back_button("menu_settings", lang="en"),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "language_ru", SettingsStates.editing_language)
async def language_ru(query: CallbackQuery, state: FSMContext, store: Store, lang: str) -> None:
    """Handle language change to Russian."""
    user_id = query.from_user.id
    # Update language in settings
    settings_service = store.SettingsService
    await settings_service.update_by_user_id(user_id, language="ru")

    # Return to settings menu
    await state.set_state(SettingsStates.in_settings)

    if query.message is None or not isinstance(query.message, Message):
        logger.error("Query message is None or not a Message", extra={"query": query})
        return

    await edit_message(
        query.message,
        state,
        t("settings.language.changed", lang="ru"),
        back_button("menu_settings", lang="ru"),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "settings_quiet_hours", SettingsStates.in_settings)
@log_action("User is editing quiet hours")
async def settings_quiet_hours(query: CallbackQuery, state: FSMContext, store: Store, lang: str, **kwargs) -> None:
    """Handle quiet hours setting."""

    await state.set_state(SettingsStates.in_quiet_hours_menu)

    if query.message is None or not isinstance(query.message, Message):
        logger.error("Query message is None or not a Message", extra={"query": query})
        return

    quiet_hours = await get_quiet_hours(query.from_user.id, store, lang)
    text = (
        f"{t('settings.quiet.hours.title', lang=lang)}\n\n"
        f"{t('settings.quiet.hours.current', lang=lang, quiet_hours=quiet_hours)}\n\n"
        f"<i>{t('settings.quiet.hours.description', lang=lang)}</i>"
    )
    await edit_message(
        query.message,
        state,
        text,
        quiet_hours_menu_inline(lang=lang),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "enable_disable_quiet_hours", SettingsStates.in_quiet_hours_menu)
async def enable_disable_quiet_hours(query: CallbackQuery, state: FSMContext, store: Store, lang: str) -> None:
    """Handle enabling/disabling quiet hours."""
    user_id = query.from_user.id
    if query.message is None or not isinstance(query.message, Message):
        logger.error("Query message is None or not a Message", extra={"query": query})
        return

    settings_service = store.SettingsService
    settings = await settings_service.get_by_user_id(user_id)
    if settings is None:
        logger.error("Settings not found", extra={"user_id": user_id})
        return

    settings = await settings_service.update_by_user_id(user_id, quiet_hours=not settings.quiet_hours)

    text = None
    if settings.quiet_hours:
        text = t("settings.quiet.hours.enabled", lang=lang)
    else:
        text = t("settings.quiet.hours.disabled", lang=lang)

    await edit_message(
        query.message,
        state,
        text,
        back_button("menu_settings", lang=lang),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "set_quite_hours", SettingsStates.in_quiet_hours_menu)
@log_action("User is entering quiet hours")
async def set_quite_hours(query: CallbackQuery, state: FSMContext, store: Store, lang: str, **kwargs) -> None:
    """Handle setting quiet hours."""

    await state.set_state(SettingsStates.waiting_for_quiet_hours_start)

    if query.message is None or not isinstance(query.message, Message):
        logger.error("Query message is None or not a Message", extra={"query": query})
        return

    text = f"{t('settings.quiet.hours.title', lang=lang)}\n\n{t('settings.quiet.hours.start.enter', lang=lang)}\n\n"

    await edit_message(
        query.message,
        state,
        text,
        back_button("menu_settings", lang=lang),
        parse_mode="HTML",
    )


@router.message(SettingsStates.waiting_for_quiet_hours_start)
async def process_quiet_hours_start_time(message: Message, state: FSMContext, store: Store, lang: str) -> None:
    """Process user's quiet hours start time and set quiet hours."""
    if message.from_user is None:
        return

    quiet_hours_start_time = message.text

    await message.delete()
    last_message = await get_last_message(state)

    if quiet_hours_start_time is None:
        quiet_hours_start_time = "nothing" if lang == "en" else "ничего"

    text = (
        f"{t('settings.quiet.hours.title', lang=lang)}\n\n"
        f"{t('settings.quiet.hours.start.enter', lang=lang)}\n\n"
        f"<i>{t('settings.quiet.hours.format.error', lang=lang, user_input=quiet_hours_start_time)}</i>"
    )
    if not is_valid_time_hhmm(quiet_hours_start_time):
        await edit_message(
            last_message,
            state,
            text,
            back_button("menu_settings", lang=lang),
            parse_mode="HTML",
        )
        return

    await state.update_data(quiet_hours_start=quiet_hours_start_time)
    await state.set_state(SettingsStates.waiting_for_quiet_hours_end)

    text = (
        f"{t('settings.quiet.hours.title', lang=lang)}\n\n"
        f"{t('settings.quiet.hours.start.entered', lang=lang, quiet_start=quiet_hours_start_time)}\n\n"
        f"{t('settings.quiet.hours.end.enter', lang=lang)}"
    )
    await edit_message(
        last_message,
        state,
        text,
        back_button("menu_settings", lang=lang),
        parse_mode="HTML",
    )


@router.message(SettingsStates.waiting_for_quiet_hours_end)
async def process_quiet_hours_end(message: Message, state: FSMContext, store: Store, lang: str) -> None:
    """Process user's quiet hours end time and set quiet hours."""
    if message.from_user is None:
        return

    quiet_hours_end = message.text

    await message.delete()
    last_message = await get_last_message(state)
    if quiet_hours_end is None:
        quiet_hours_end = "nothing" if lang == "en" else "ничего"

    quiet_hours_start = (await state.get_data()).get("quiet_hours_start")
    if quiet_hours_start is None:
        logger.error("Quiet hours start time is not set", extra={"state": await state.get_data()})
        return

    text = (
        f"{t('settings.quiet.hours.title', lang=lang)}\n\n"
        f"{t('settings.quiet.hours.start.entered', lang=lang, quiet_start=quiet_hours_start)}\n\n"
        f"{t('settings.quiet.hours.end.enter', lang=lang)}\n\n"
        f"<i>{t('settings.quiet.hours.format.error', lang=lang, user_input=quiet_hours_end)}</i>"
    )
    if not is_valid_time_hhmm(quiet_hours_end):
        await edit_message(
            last_message,
            state,
            text,
            back_button("menu_settings", lang=lang),
            parse_mode="HTML",
        )
        return

    if quiet_hours_start == quiet_hours_end:
        text = (
            f"{t('settings.quiet.hours.title', lang=lang)}\n\n"
            f"{t('settings.quiet.hours.start.entered', lang=lang, quiet_start=quiet_hours_start)}\n\n"
            f"{t('settings.quiet.hours.end.enter', lang=lang, quiet_end=quiet_hours_end)}\n\n"
            f"<i>{t('settings.quiet.hours.equal.error', lang=lang)}</i>"
        )
        await edit_message(
            last_message,
            state,
            text,
            back_button("menu_settings", lang=lang),
            parse_mode="HTML",
        )
        return

    await state.update_data(quiet_hours_end=quiet_hours_end)
    await state.set_state(SettingsStates.in_settings)
    text = (
        f"{t('settings.quiet.hours.title', lang=lang)}\n\n"
        f"<i>{t('settings.quiet.hours.accept.reject', lang=lang, quiet_start=quiet_hours_start, quiet_end=quiet_hours_end)}</i>"  # noqa: E501
    )
    await edit_message(
        last_message,
        state,
        text,
        quiet_hours_accept_reject_inline(lang=lang),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "accept_quiet_hours", SettingsStates.in_settings)
async def accept_quiet_hours(query: CallbackQuery, state: FSMContext, store: Store, lang: str) -> None:
    """Handle accepting quiet hours."""
    user_id = query.from_user.id
    if query.message is None or not isinstance(query.message, Message):
        logger.error("Query message is None or not a Message", extra={"query": query})
        return

    quiet_hours_start = (await state.get_data()).get("quiet_hours_start")
    quiet_hours_end = (await state.get_data()).get("quiet_hours_end")

    settings_service = store.SettingsService
    await settings_service.update_by_user_id(
        user_id, quiet_hours=True, quiet_hours_start=quiet_hours_start, quiet_hours_end=quiet_hours_end
    )
    await state.set_state(SettingsStates.in_settings)
    await edit_message(
        query.message,
        state,
        t("settings.quiet.hours.accepted", lang=lang),
        back_button("menu_settings", lang=lang),
    )


async def get_daily_plan_time(user_id: int, store: Store, lang: str) -> str:
    settings = await store.SettingsService.get_by_user_id(user_id)
    if settings is None or settings.daily_plans_time is None:
        return "Disabled" if lang == "en" else "Отключено"

    return settings.daily_plans_time.strftime("%H:%M")


@router.callback_query(F.data == "settings_daily_plans_time", SettingsStates.in_settings)
@log_action("User is editing daily plans time")
async def settings_daily_plans_time(query: CallbackQuery, state: FSMContext, store: Store, lang: str, **kwargs) -> None:
    """Handle daily plans time setting."""
    await state.set_state(SettingsStates.editing_daily_plans_time)

    if query.message is None or not isinstance(query.message, Message):
        logger.error("Query message is None or not a Message", extra={"query": query})
        return

    daily_plan_time = await get_daily_plan_time(query.from_user.id, store, lang)

    text = (
        f"{t('settings.daily.plans.time.title', lang=lang)}\n\n"
        f"{t('settings.daily.plans.time.current', lang=lang, daily_plan=daily_plan_time)}\n\n"
        f"{t('settings.daily.plans.time.enter', lang=lang)}"
    )

    await edit_message(
        query.message,
        state,
        text,
        back_button("menu_settings", lang=lang),
        parse_mode="HTML",
    )


@router.message(SettingsStates.editing_daily_plans_time)
async def process_daily_plans_time(message: Message, state: FSMContext, store: Store, lang: str) -> None:
    """Process user's daily plans time and set daily plans time."""
    if message.from_user is None:
        return

    daily_plans_time = message.text

    await message.delete()
    last_message = await get_last_message(state)

    if daily_plans_time is None:
        daily_plans_time = "nothing" if lang == "en" else "ничего"

    text = (
        f"{t('settings.daily.plans.time.title', lang=lang)}\n\n"
        f"{t('settings.daily.plans.time.enter', lang=lang)}\n\n"
        f"<i>{t('settings.daily.plans.time.format.error', lang=lang, user_input=daily_plans_time)}</i>"
    )
    if not is_valid_time_hhmm(daily_plans_time):
        await edit_message(
            last_message,
            state,
            text,
            back_button("menu_settings", lang=lang),
            parse_mode="HTML",
        )
        return

    await state.update_data(daily_plans_time=daily_plans_time)
    await state.set_state(SettingsStates.in_settings)
    text = (
        f"{t('settings.daily.plans.time.title', lang=lang)}\n\n"
        f"<i>{t('settings.daily.plans.time.accept.reject', lang=lang, daily_plan=daily_plans_time)}</i>"
    )
    await edit_message(
        last_message,
        state,
        text,
        daily_plans_time_accept_reject_inline(lang=lang),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "accept_daily_plans_time", SettingsStates.in_settings)
async def accept_daily_plans_time(query: CallbackQuery, state: FSMContext, store: Store, lang: str) -> None:
    """Handle accepting daily plans time."""
    user_id = query.from_user.id
    if query.message is None or not isinstance(query.message, Message):
        logger.error("Query message is None or not a Message", extra={"query": query})
        return

    daily_plans_time = (await state.get_data()).get("daily_plans_time")
    settings_service = store.SettingsService
    await settings_service.update_by_user_id(user_id, daily_plans_time=daily_plans_time)
    await state.set_state(SettingsStates.in_settings)
    await edit_message(
        query.message,
        state,
        t("settings.daily.plans.time.accepted", lang=lang),
        back_button("menu_settings", lang=lang),
        parse_mode="HTML",
    )
