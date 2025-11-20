from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from i18n.strings import t
from keyboards.inline import (
    create_calendar,
    get_back_button,
    get_events_create_inline,
    get_events_menu_inline,
)
from logger.logger import logger
from states.states import EventsMenuStates

router = Router()


@router.callback_query(F.data == "menu_events")
async def open_events_menu(query: CallbackQuery, state: FSMContext) -> None:
    """Open events menu."""
    user_id = query.from_user.id
    logger.info(f"User {user_id} opened events menu")

    # TODO: Get user language from settings when session is available
    lang = "ru"

    await state.set_state(EventsMenuStates.in_events_menu)

    if query.message and hasattr(query.message, "edit_text"):
        await query.message.edit_text(
            t("events.title", lang=lang),
            parse_mode="HTML",
            reply_markup=get_events_menu_inline(lang=lang),
        )


@router.callback_query(F.data == "events_import", EventsMenuStates.in_events_menu)
async def events_import(query: CallbackQuery, state: FSMContext) -> None:
    """Open import feature"""
    user_id = query.from_user.id
    logger.info(f"User {user_id} is importing events")

    # TODO: Get user language from settings when session is available
    lang = "ru"

    await state.set_state(EventsMenuStates.in_events_import)
    await query.answer(t("events.import.selected", lang=lang))

    if query.message and hasattr(query.message, "edit_text"):
        text = (
            f"{t('events.import.title', lang=lang)}\n\n"
            "{t('events.import.description', lang=lang)}\n\n"
            "<i>{t('events.feature_dev', lang=lang)}</i>"
        )
        await query.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=get_back_button("menu_events", lang=lang),
        )


@router.callback_query(F.data == "events_export", EventsMenuStates.in_events_menu)
async def events_export(query: CallbackQuery, state: FSMContext) -> None:
    """Open export feature"""
    user_id = query.from_user.id
    logger.info(f"User {user_id} is exporting events")

    # TODO: Get user language from settings when session is available
    lang = "ru"

    await state.set_state(EventsMenuStates.in_events_export)
    await query.answer(t("events.export.selected", lang=lang))

    if query.message and hasattr(query.message, "edit_text"):
        text = (
            f"{t('events.export.title', lang=lang)}\n\n"
            "{t('events.export.description', lang=lang)}\n\n"
            "<i>{t('events.feature_dev', lang=lang)}</i>"
        )
        await query.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=get_back_button("menu_events", lang=lang),
        )


@router.callback_query(F.data == "events_create", EventsMenuStates.in_events_menu)
async def events_create(query: CallbackQuery, state: FSMContext) -> None:
    """Open event creation feature"""
    user_id = query.from_user.id
    logger.info(f"User {user_id} is choosing creating event option")

    # TODO: Get user language from settings when session is available
    lang = "ru"

    await state.set_state(EventsMenuStates.in_events_create)
    await query.answer(t("events.create.selected", lang=lang))

    if query.message and hasattr(query.message, "edit_text"):
        text = f"{t('events.create.title', lang=lang)}\n\n<i>{t('events.feature_dev', lang=lang)}</i>"
        await query.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=get_events_create_inline(lang=lang),
        )


@router.callback_query(F.data == "events_view", EventsMenuStates.in_events_menu)
async def events_view(query: CallbackQuery, state: FSMContext) -> None:
    """Open event view feature"""
    user_id = query.from_user.id
    logger.info(f"User {user_id} is viewing events")

    # TODO: Get user language from settings when session is available
    lang = "ru"

    await state.set_state(EventsMenuStates.in_events_view)
    await query.answer(t("events.view.selected", lang=lang))

    if query.message and hasattr(query.message, "edit_text"):
        text = f"{t('events.view.title', lang=lang)}\n\n<i>{t('events.feature_dev', lang=lang)}</i>"
        await query.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=create_calendar(lang=lang),
        )
