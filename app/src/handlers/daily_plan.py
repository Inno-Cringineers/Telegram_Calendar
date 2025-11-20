from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from keyboards.inline import get_back_button, get_notification_inline
from logger.logger import logger

router = Router()


@router.callback_query(F.data == "menu_daily_plan")
async def get_daily_plan(query: CallbackQuery, state: FSMContext):
    """Send daily plan to user."""
    user_id = query.from_user.id
    logger.info(f"User {user_id} requested daily plan")

    await query.answer("📋 Generating daily plan...")

    daily_plan = """
📋 <b>Your Plan for the day - November 15, 2025</b>
"""
    event_1 = """
Meeting with the client
"At meeting room 110"
09:00-11:00
Don’t repeat
30 min before remind
source: Outlook (Link to calendar)
"""
    event_2 = """
Lunch with colleagues
12:00-13:00
Repeat every 1 day
15 min before remind
source: Personal calendar
"""
    event_3 = """
Presentation of the Project
15:30-17:00
Don’t repeat
1 hour before remind
source: Google calendar (link to calendar)
    """
    event_4 = """
House choirs
20:30-22:00
Don’t repeat
10 minutes before remind
source: Personal calendar
    """

    if query.message and hasattr(query.message, "answer"):
        await query.message.answer(
            daily_plan,
            parse_mode="HTML",
        )

    if query.message and hasattr(query.message, "answer"):
        await query.message.answer(
            event_1,
            parse_mode="HTML",
        )

    if query.message and hasattr(query.message, "answer"):
        await query.message.answer(
            event_2,
            parse_mode="HTML",
            reply_markup=get_notification_inline(),
        )

    if query.message and hasattr(query.message, "answer"):
        await query.message.answer(
            event_3,
            parse_mode="HTML",
        )

    if query.message and hasattr(query.message, "answer"):
        await query.message.answer(
            event_4,
            parse_mode="HTML",
            reply_markup=get_notification_inline(),
        )

    if query.message and hasattr(query.message, "answer"):
        await query.message.answer(
            "End of daily plan",
            reply_markup=get_back_button("back_to_main"),
        )
