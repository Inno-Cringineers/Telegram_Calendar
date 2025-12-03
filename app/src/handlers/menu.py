from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from i18n.strings import t
from keyboards.inline import main_menu_inline
from logger.logger import logger
from states.states import MainMenuStates

router = Router()


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext, lang: str) -> None:
    """Open main menu."""
    user_id = message.from_user.id if message.from_user else None
    logger.info(f"User {user_id} opened main menu")

    user_name = message.from_user.first_name if message.from_user else "User"
    welcome_text = t("start.welcome", lang=lang, user_name=user_name)

    await state.set_state(MainMenuStates.in_main_menu)
    await message.answer(
        welcome_text,
        parse_mode="HTML",
        reply_markup=main_menu_inline(lang=lang),
    )


@router.callback_query(F.data == "back_to_main")
async def back_to_main(query: CallbackQuery, state: FSMContext, lang: str) -> None:
    """Go back to main menu from any submenu."""
    user_id = query.from_user.id
    logger.debug(f"User {user_id} going back to main menu")

    user_name = query.from_user.first_name if query.from_user else "User"
    welcome_text = t("start.welcome", lang=lang, user_name=user_name)

    await state.set_state(MainMenuStates.in_main_menu)

    # Get the message safely
    if query.message and isinstance(query.message, Message):
        await query.message.edit_text(
            welcome_text,
            parse_mode="HTML",
            reply_markup=main_menu_inline(lang=lang),
        )
    else:
        await query.answer(t("menu.updated", lang=lang))
