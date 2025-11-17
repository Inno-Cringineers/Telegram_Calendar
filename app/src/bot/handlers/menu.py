from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.states.states import MainMenuStates
from bot.keyboards.inline import get_main_menu_inline
from bot.logger import logger

router = Router()


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext):
    """Open main menu."""
    user_id = message.from_user.id if message.from_user else None
    logger.info(f"User {user_id} opened main menu")

    await state.set_state(MainMenuStates.in_main_menu)
    await message.answer(
        "🏠 <b>Main Menu</b>\n\nChoose an option:",
        parse_mode="HTML",
        reply_markup=get_main_menu_inline(),
    )


@router.callback_query(F.data == "back_to_main")
async def back_to_main(query: CallbackQuery, state: FSMContext):
    """Go back to main menu from any submenu."""
    user_id = query.from_user.id
    logger.debug(f"User {user_id} going back to main menu")

    await state.set_state(MainMenuStates.in_main_menu)

    # Get the message safely
    if query.message and hasattr(query.message, "edit_text"):
        await query.message.edit_text(
            "🏠 <b>Main Menu</b>\n\nChoose an option:",
            parse_mode="HTML",
            reply_markup=get_main_menu_inline(),
        )
    else:
        await query.answer("Menu updated")
