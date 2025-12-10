from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from i18n.strings import t
from keyboards.inline import (
    back_button,
    create_calendar,
    events_create_inline,
    events_menu_inline,
)
from logger.logger import logger
from states.states import EventsMenuStates
from utils.handlers import clean_messages, edit_message

router = Router()


@router.callback_query(F.data == "menu_events")
async def open_events_menu(query: CallbackQuery, state: FSMContext, lang: str) -> None:
    """Open events menu."""

    await state.set_state(EventsMenuStates.in_events_menu)

    await clean_messages(query.bot, query.message.chat.id, state)

    await edit_message(
        query.bot,
        query.message.chat.id,
        query.message.message_id,
        state,
        t("events.title", lang=lang),
        events_menu_inline(lang=lang),
        parse_mode="HTML",
        delete_keyboard=True,
        delete_message=False,
    )


@router.callback_query(F.data == "events_import", StateFilter(EventsMenuStates.in_events_menu))
async def events_import(query: CallbackQuery, state: FSMContext, lang: str) -> None:
    """Open import feature"""
    user_id = query.from_user.id
    logger.info(f"User {user_id} is importing events")

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
            reply_markup=back_button("menu_events", lang=lang),
        )


@router.callback_query(F.data == "events_export", StateFilter(EventsMenuStates.in_events_menu))
async def events_export(query: CallbackQuery, state: FSMContext, lang: str) -> None:
    """Open export feature"""
    user_id = query.from_user.id
    logger.info(f"User {user_id} is exporting events")

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
            reply_markup=back_button("menu_events", lang=lang),
        )


@router.callback_query(F.data == "events_create", StateFilter(EventsMenuStates.in_events_menu))
async def events_create(query: CallbackQuery, state: FSMContext, lang: str) -> None:
    """Open event creation feature"""
    user_id = query.from_user.id
    logger.info(f"User {user_id} is choosing creating event option")

    await state.set_state(EventsMenuStates.in_events_create)
    await query.answer(t("events.create.selected", lang=lang))

    if query.message and hasattr(query.message, "edit_text"):
        text = f"{t('events.create.title', lang=lang)}\n\n<i>{t('events.feature_dev', lang=lang)}</i>"
        await query.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=events_create_inline(lang=lang),
        )


@router.callback_query(F.data == "events_view", StateFilter(EventsMenuStates.in_events_menu))
async def events_view(query: CallbackQuery, state: FSMContext, lang: str) -> None:
    """Open event view feature"""
    user_id = query.from_user.id
    logger.info(f"User {user_id} is viewing events")

    await state.set_state(EventsMenuStates.in_events_view)
    await query.answer(t("events.view.selected", lang=lang))

    if query.message and hasattr(query.message, "edit_text"):
        text = f"{t('events.view.title', lang=lang)}\n\n<i>{t('events.feature_dev', lang=lang)}</i>"
        await query.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=create_calendar(lang=lang),
        )
