"""Handler for /start command and deep-link processing.

This module handles the bot's start command, welcoming users and processing
deep-links for timezone selection.
"""

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from i18n.strings import t
from keyboards.inline import back_button, main_menu_inline
from states.states import MainMenuStates
from utils.handlers import (
    clean_messages,
    send_message,
)

router = Router()


@router.message(Command("help"))
async def help_handler(message: Message, state: FSMContext, lang: str) -> None:
    """Handle /help command. Shows help placeholder message."""
    await state.set_state(MainMenuStates.in_main_menu)

    await clean_messages(message.bot, message.chat.id, state, delete_all=True)

    help_text = t("help.message", lang=lang)

    await send_message(
        message.bot,
        message.chat.id,
        state,
        help_text,
        back_button("back_to_main", lang=lang),
        parse_mode="HTML",
        delete_keyboard=True,
    )


@router.message(Command("start"))
async def start_handler(message: Message, state: FSMContext, lang: str) -> None:
    """Handle /start command. Welcomes the user with bot information and main menu."""
    username = message.from_user.first_name if message.from_user else "User"

    await state.set_state(MainMenuStates.in_main_menu)

    await clean_messages(message.bot, message.chat.id, state, delete_all=True)

    await send_message(
        message.bot,
        message.chat.id,
        state,
        t("start.welcome", lang=lang, user_name=username),
        main_menu_inline(lang=lang),
        parse_mode="HTML",
        delete_keyboard=True,
    )


@router.callback_query(F.data == "back_to_main")
async def back_to_main(query: CallbackQuery, state: FSMContext, lang: str) -> None:
    """Go back to main menu from any submenu."""

    username = query.from_user.first_name if query.from_user else "User"

    await state.set_state(MainMenuStates.in_main_menu)

    # Clean all messages from previous contexts
    await clean_messages(query.bot, query.message.chat.id, state, delete_all=True)

    # Send new main menu message instead of editing (because the original message might be deleted)
    await send_message(
        query.bot,
        query.message.chat.id,
        state,
        t("start.welcome", lang=lang, user_name=username),
        main_menu_inline(lang=lang),
        parse_mode="HTML",
        delete_keyboard=True,
        delete_message=False,  # Main menu message should persist
    )
