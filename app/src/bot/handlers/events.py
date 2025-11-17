from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from bot.states.states import EventsMenuStates
from bot.keyboards.inline import *
from bot.logger import logger

router = Router()


@router.callback_query(F.data == "menu_events")
async def open_events_menu(query: CallbackQuery, state: FSMContext):
    """Open events menu."""
    user_id = query.from_user.id
    logger.info(f"User {user_id} opened events menu")

    await state.set_state(EventsMenuStates.in_events_menu)

    if query.message and hasattr(query.message, "edit_text"):
        await query.message.edit_text(
            "📅 <b>Events</b>\n\nChoose an events option:",
            parse_mode="HTML",
            reply_markup=get_events_menu_inline(),
        )


@router.callback_query(F.data == "events_import", EventsMenuStates.in_events_menu)
async def events_import(query: CallbackQuery, state: FSMContext):
    """Open import feature"""
    user_id = query.from_user.id
    logger.info(f"User {user_id} is importing events")

    await state.set_state(EventsMenuStates.in_events_import)
    await query.answer("📥 Event import selected")

    if query.message and hasattr(query.message, "edit_text"):
        await query.message.edit_text(
            "📥 <b>Events import</b>\n\n"
            "Please load file in .ics format to the chat\n\n"
            "<i>Feature is under development.</i>",
            parse_mode="HTML",
            reply_markup=get_back_button("menu_events"),
        )


@router.callback_query(F.data == "events_export", EventsMenuStates.in_events_menu)
async def events_export(query: CallbackQuery, state: FSMContext):
    """Open export feature"""
    user_id = query.from_user.id
    logger.info(f"User {user_id} is exporting events")

    await state.set_state(EventsMenuStates.in_events_export)
    await query.answer("📥 Event export selected")

    if query.message and hasattr(query.message, "edit_text"):
        await query.message.edit_text(
            "📥 <b>Events export</b>\n\n"
            "This is your events in .ics format (only internal events)\n\n"
            "<i>Feature is under development.</i>",
            parse_mode="HTML",
            reply_markup=get_back_button("menu_events"),
        )


@router.callback_query(F.data == "events_create", EventsMenuStates.in_events_menu)
async def events_create(query: CallbackQuery, state: FSMContext):
    """Open event creation feature"""
    user_id = query.from_user.id
    logger.info(f"User {user_id} is choosing creating event option")

    await state.set_state(EventsMenuStates.in_events_create)
    await query.answer("➕ Event creation selected")

    if query.message and hasattr(query.message, "edit_text"):
        await query.message.edit_text(
            "➕ <b>Events creation</b>\n\n<i>Feature is under development.</i>",
            parse_mode="HTML",
            reply_markup=get_events_create_inline(),
        )


@router.callback_query(F.data == "events_view", EventsMenuStates.in_events_menu)
async def events_view(query: CallbackQuery, state: FSMContext):
    """Open event view feature"""
    user_id = query.from_user.id
    logger.info(f"User {user_id} is viewing events")

    await state.set_state(EventsMenuStates.in_events_view)
    await query.answer("🔍 Events viewing selected")

    if query.message and hasattr(query.message, "edit_text"):
        await query.message.edit_text(
            "🔍 <b>Events viewing</b>\n\n<i>Feature is under development.</i>",
            parse_mode="HTML",
            reply_markup=create_calendar(),
        )
