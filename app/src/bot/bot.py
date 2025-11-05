from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from .config import Config

async def setup_bot(config: Config) -> Bot:

    bot = Bot(token=config.telegram_token)
    dp = Dispatcher()

    @dp.message(Command("start"))
    async def start_handler(message: Message):
        await message.answer(
            "👋 Hello! I'm your personal Calendar bot!\n"
            "This is a version that simply says hello world!"
        )

    await dp.start_polling(bot)
    
    return bot