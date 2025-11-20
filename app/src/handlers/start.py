"""Handler for /start command and deep-link processing.

This module handles the bot's start command, welcoming users and processing
deep-links for timezone selection.
"""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from i18n.strings import t
from keyboards.inline import get_main_menu_inline
from logger.logger import logger

router = Router()


@router.message(Command("start"))
async def start_handler(message: Message) -> None:
    """Handle /start command and deep-link processing.

    Processes both regular /start command and deep-links (e.g., ?start=tz_utc3).
    For regular start, welcomes the user with bot information and main menu.
    For deep-links, processes timezone selection (currently placeholder).

    Args:
        message: Incoming message with /start command.

    Returns:
        None. Sends welcome message or processes deep-link.
    """
    # Deep-Link handler (for timezones)
    # checking 'tz_utc3' from ?start=tz_utc3
    if message.text is None:
        return

    parts = message.text.split(maxsplit=1)
    payload = parts[1] if len(parts) > 1 else None

    if payload:
        # Process payload
        if message.from_user is None:
            return
        deep_link_user_id = message.from_user.id
        logger.info(f"User {deep_link_user_id} clicked deep-link: {payload}")

        # Delete message /start
        await message.delete()

        # TODO: go to deep-link handler

        return

    # Regular /start handler
    user_name = message.from_user.first_name if message.from_user else "User"
    user_id: int | None = message.from_user.id if message.from_user else None

    logger.info(f"User {user_name} (ID: {user_id}) started the bot")

    # TODO: Get user language from settings when session is available
    lang = "ru"
    welcome_text = t("start.welcome", lang=lang, user_name=user_name)

    await message.answer(
        text=welcome_text,
        parse_mode="HTML",
        reply_markup=get_main_menu_inline(lang=lang),
    )
