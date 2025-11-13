from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

router = Router()


@router.message(Command("start"))
async def start_handler(message: Message, session: AsyncSession):
    user_name = message.from_user.first_name if message.from_user else "User"
    
    welcome_text = f"""
👋 Welcome to Telegram Calendar, {user_name}!

I can help you manage your calendar events. Here are the available commands:

/start - Show this welcome message
/help - Get help with available commands
/new - Create a new event
/list - View your upcoming events
/delete - Delete an event
/settings - Customize your preferences

Let's get started! Use /new to create your first event.
    """.strip()
    
    await message.answer(welcome_text)
