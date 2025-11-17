from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from bot.states.states import CalendarLinkingStates
from bot.keyboards.inline import get_calendar_menu_inline, get_back_button
from bot.logger import logger

router = Router()


@router.callback_query(F.data == "menu_link_calendar")
async def open_calendar_menu(query: CallbackQuery, state: FSMContext):
    """Open calendar linking menu."""
    user_id = query.from_user.id
    logger.info(f"User {user_id} opened calendar menu")

    await state.set_state(CalendarLinkingStates.in_calendar_menu)

    if query.message and hasattr(query.message, "edit_text"):
        await query.message.edit_text(
            "🔗 <b>Link a Calendar</b>\n\nChoose an action:",
            parse_mode="HTML",
            reply_markup=get_calendar_menu_inline(),
        )


@router.callback_query(F.data == "calendar_list", CalendarLinkingStates.in_calendar_menu)
async def calendar_list(query: CallbackQuery, state: FSMContext):
    """Show list of linked calendars."""
    user_id = query.from_user.id
    logger.info(f"User {user_id} viewing calendar list")

    await state.set_state(CalendarLinkingStates.in_calendar_list)
    await query.answer("📑 Your calendars")

    if query.message and hasattr(query.message, "edit_text"):
        await query.message.edit_text(
            "📑 <b>Your Calendars</b>\n\n"
            "<b>Linked Calendars:</b>\n"
            "1. 📅 Personal (Google Calendar)\n"
            "2. 💼 Work (Outlook Calendar)\n"
            "3. 🎯 Projects (Yandex Calendar)\n\n"
            "<i>Feature is under development. You can unlink calendars here.</i>",
            parse_mode="HTML",
            reply_markup=get_back_button(),
        )


@router.callback_query(F.data == "calendar_new", CalendarLinkingStates.in_calendar_menu)
async def calendar_new(query: CallbackQuery, state: FSMContext):
    """Link a new calendar."""
    user_id = query.from_user.id
    logger.info(f"User {user_id} initiated linking new calendar")

    await state.set_state(CalendarLinkingStates.waiting_for_calendar_link)
    await query.answer("🔗 Link new calendar")

    if query.message and hasattr(query.message, "edit_text"):
        await query.message.edit_text(
            "🔗 <b>Link a New Calendar</b>\n\n<b>Enter the ical link:</b>\n\n<i>Feature is under development.</i>",
            parse_mode="HTML",
            reply_markup=get_back_button(),
        )
