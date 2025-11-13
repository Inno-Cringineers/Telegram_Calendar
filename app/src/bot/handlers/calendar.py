from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from bot.states.event import CalendarLinkingStates
from bot.keyboards.inline import get_calendar_menu_inline, get_back_button
from bot.logger import logger

router = Router()


@router.callback_query(F.data == "menu_daily_plan")
async def get_daily_plan(query: CallbackQuery):
    """Send daily plan to user."""
    user_id = query.from_user.id
    logger.info(f"User {user_id} requested daily plan")
    
    await query.answer("📋 Generating daily plan...")
    
    # Mock daily plan data
    daily_plan = """
📋 <b>Your Daily Plan - November 13, 2025</b>

<b>Morning (08:00 - 12:00)</b>
• 09:00 - Team standup meeting (30 min)
• 10:00 - Work on feature X
• 12:00 - Lunch break

<b>Afternoon (12:00 - 18:00)</b>
• 14:00 - Client call (1 hour)
• 15:00 - Code review
• 17:00 - Daily summary

<b>Evening (18:00 - 22:00)</b>
• 19:00 - Personal time
• 20:00 - Free

<b>Summary:</b>
✅ 3 important events
⏱️ 2.5 hours of meetings
📊 3 hours of focused work
    """.strip()
    
    # Send as a new message (not edit)
    await query.message.chat.send_message(
        daily_plan,
        parse_mode="HTML",
    )
    await query.answer("✅ Daily plan sent!")


@router.callback_query(F.data == "menu_link_calendar")
async def open_calendar_menu(query: CallbackQuery, state: FSMContext):
    """Open calendar linking menu."""
    user_id = query.from_user.id
    logger.info(f"User {user_id} opened calendar menu")
    
    await state.set_state(CalendarLinkingStates.in_calendar_menu)
    
    if query.message and hasattr(query.message, 'edit_text'):
        await query.message.edit_text(
            "🔗 <b>Link a Calendar</b>\n\n"
            "Choose an action:",
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
    
    if query.message and hasattr(query.message, 'edit_text'):
        await query.message.edit_text(
            "📑 <b>Your Calendars</b>\n\n"
            "<b>Linked Calendars:</b>\n"
            "1. 📅 Personal (Google Calendar)\n"
            "2. 💼 Work (Outlook Calendar)\n"
            "3. 🎯 Projects (Mocked)\n\n"
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
    
    if query.message and hasattr(query.message, 'edit_text'):
        await query.message.edit_text(
            "🔗 <b>Link a New Calendar</b>\n\n"
            "<b>Supported Services:</b>\n"
            "• 🔵 Google Calendar\n"
            "• 🔴 Outlook Calendar\n"
            "• 📱 Apple Calendar\n\n"
            "<i>Feature is under development. Send the calendar URL or select a service.</i>",
            parse_mode="HTML",
            reply_markup=get_back_button(),
        )
