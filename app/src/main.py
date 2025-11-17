import asyncio

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import load_config
from bot.database import get_engine, get_session_maker, init_db
from bot.logger import logger, setup_logger
from bot.middlewares.database_middlware import DatabaseMiddleware
from bot.middlewares.logging_middleware import (
    CallbackQueryLoggingMiddleware,
    MessageLoggingMiddleware,
)
from bot.router import router


async def setup_database(dp: Dispatcher, db_url: str):
    """Setup database and inject session middleware."""
    engine = get_engine(db_url)
    await init_db(engine)
    session_maker = get_session_maker(engine)

    # Middleware to inject database session in handlers
    dp.message.middleware(DatabaseMiddleware(session_maker))
    dp.callback_query.middleware(DatabaseMiddleware(session_maker))


def setup_middlewares(dp: Dispatcher):
    """Setup all middlewares for dispatcher."""
    # Logging middlewares
    dp.message.outer_middleware(MessageLoggingMiddleware())
    dp.callback_query.outer_middleware(CallbackQueryLoggingMiddleware())

    logger.debug("Middlewares setup completed")


async def main():
    cfg = load_config()

    # Setup logger with config
    setup_logger(cfg.logger)

    logger.info("Starting Telegram Calendar Bot...")
    logger.info(f"Logger level: {cfg.logger.level}")

    bot = Bot(cfg.telegram_token)
    dp = Dispatcher(storage=MemoryStorage())

    await setup_database(dp, cfg.db_url)
    setup_middlewares(dp)

    dp.include_router(router)

    logger.info("Bot is running...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
