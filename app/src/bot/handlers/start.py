from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.keyboards.inline import get_main_menu_inline
from bot.logger import logger

router = Router()


@router.message(Command("start"))
async def start_handler(message: Message):
    # This is Deep-Link handler (for timezones)
    # -----------------------------
    # checking 'tz_utc3' из ?start=tz_utc3
    if message.text is None:
        return

    parts = message.text.split(maxsplit=1)
    payload = parts[1] if len(parts) > 1 else None

    if payload:
        # process payload
        if message.from_user is None:
            return
        user_id = message.from_user.id
        logger.info(f"User {user_id} clicked deep-link: {payload}")

        # delete message /start
        await message.delete()

        # TODO: go to deep-link handler

        return

    # -------------------------------

    # This is /start handler
    """Handler for /start command. Welcomes the user and provides basic information."""
    user_name = message.from_user.first_name if message.from_user else "User"
    user_id = message.from_user.id if message.from_user else None

    logger.info(f"User {user_name} (ID: {user_id}) started the bot")

    welcome_text = f"""
👋 <b>Welcome to the Telegram Calendar reminder, {user_name}!</b>

I can help to manage your events and reminders, even from external calendars.

📋 <b>Commands:</b>
/start - Show this dialog
/help - Get help
/menu - Open main menu

🎯 <b>Main functions:</b>
• 📅 Events viewing
• ➕ Creating events
• ✏️ Editing events
• 🗑️ Deleting events
• 🔗 Exporting external calendars (google, outlook, etc.)
• ⏰ Events reminders
• 📋 Daily planss

    """.strip()

    await message.answer(
        welcome_text,
        parse_mode="HTML",
        reply_markup=get_main_menu_inline(),
    )
