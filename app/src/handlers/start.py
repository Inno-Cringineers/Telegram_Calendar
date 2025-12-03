"""Handler for /start command and deep-link processing.

This module handles the bot's start command, welcoming users and processing
deep-links for timezone selection.
"""

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from i18n.strings import t
from keyboards.inline import main_menu_inline
from states.states import MainMenuStates
from utils.handlers import log_action, send_clean_message

router = Router()


@router.message(Command("start"))
@log_action("User started the bot")
async def start_handler(message: Message, state: FSMContext, lang: str, **kwargs) -> None:
    """Handle /start command. Welcomes the user with bot information and main menu."""
    username = message.from_user.first_name if message.from_user else "User"

    await state.set_state(MainMenuStates.in_main_menu)
    await send_clean_message(
        message,
        state,
        t("start.welcome", lang=lang, user_name=username),
        main_menu_inline(lang=lang),
        parse_mode="HTML",
    )
