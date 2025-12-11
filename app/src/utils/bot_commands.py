"""Utility functions for setting up bot commands."""

from aiogram import Bot
from aiogram.types import BotCommand

from i18n.strings import t
from logger.logger import logger


async def setup_bot_commands(bot: Bot) -> None:
    """Set up bot commands menu for all supported languages.

    This function sets the list of commands that will appear in the bot's
    command menu when users type "/" in the chat.

    Args:
        bot: Bot instance.
    """
    # Default commands (English)
    commands_en = [
        BotCommand(command="start", description=t("command.start.description", lang="en")),
        BotCommand(command="help", description=t("command.help.description", lang="en")),
    ]

    # Russian commands
    commands_ru = [
        BotCommand(command="start", description=t("command.start.description", lang="ru")),
        BotCommand(command="help", description=t("command.help.description", lang="ru")),
    ]

    try:
        # Set default commands (for users without language preference)
        await bot.set_my_commands(commands_en)
        logger.info("Bot commands set (default/English)")

        # Set commands for Russian language
        await bot.set_my_commands(commands_ru, language_code="ru")
        logger.info("Bot commands set (Russian)")

    except Exception as e:
        logger.error("Failed to set bot commands: %s", e, exc_info=True)

