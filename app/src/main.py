import asyncio

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from config.config import load_config
from database.database import create_engine, create_session_maker, create_tables
from logger.logger import logger, setup_logger
from middlewares.logging_middleware import (
    CallbackQueryLoggingMiddleware,
    MessageLoggingMiddleware,
)
from middlewares.settings_middleware import SettingsMiddleware
from middlewares.store_middlware import StoreMiddleware
from router.router import router
from services.daily_plan_scheduler import init_daily_plan_scheduler
from services.reminder_scheduler import init_reminder_scheduler
from services.sync_service import SyncService


async def setup_database_and_store(db_url: str) -> async_sessionmaker[AsyncSession]:
    """Setup database and return session maker.

    Args:
        db_url: Database connection URL.

    Returns:
        Session maker for creating database sessions.
    """
    # Create async SQLAlchemy engine
    engine = create_engine(db_url)
    # Create tables
    await create_tables(engine)
    # Create session maker
    session_maker = create_session_maker(engine)

    return session_maker


def setup_middlewares(dp: Dispatcher) -> None:
    """Setup all middlewares for dispatcher."""
    # Logging middlewares
    dp.message.outer_middleware(MessageLoggingMiddleware())
    dp.callback_query.outer_middleware(CallbackQueryLoggingMiddleware())
    # Settings middleware
    dp.message.middleware(SettingsMiddleware())
    dp.callback_query.middleware(SettingsMiddleware())
    logger.debug("Middlewares setup completed")


async def main() -> None:
    # Load config
    cfg = load_config()

    # Setup logger with config
    setup_logger(cfg.logger)

    logger.info("Starting Telegram Calendar Bot")
    logger.debug("Config:")
    logger.debug(f"Bot token: {cfg.bot.telegram_token}")
    logger.debug(f"Database URL: {cfg.database.url}")
    logger.debug(f"Logger level: {cfg.logger.level}")
    logger.debug(f"Logger console: {cfg.logger.console}")
    logger.debug(f"Logger file: {cfg.logger.file_enabled}")
    logger.debug(f"Logger file path: {cfg.logger.file_path}")
    logger.debug(f"Logger file max bytes: {cfg.logger.max_bytes}")
    logger.debug(f"Logger file backup count: {cfg.logger.backup_count}")
    logger.debug(f"Bot timeout: {cfg.bot.timeout}")
    logger.debug(f"Bot single user: {cfg.bot.single_user}")

    # Create bot
    bot = Bot(token=cfg.bot.telegram_token)
    # Create dispatcher
    dp = Dispatcher(storage=MemoryStorage())
    # TODO: Add Redis storage for FSM
    # Setup database
    session_maker = await setup_database_and_store(cfg.database.url)
    # Setup reminder scheduler
    reminder_scheduler = init_reminder_scheduler(session_maker, bot)
    daily_plan_scheduler = init_daily_plan_scheduler(session_maker, bot)
    # Setup store middleware
    dp.message.middleware(StoreMiddleware(session_maker))
    dp.callback_query.middleware(StoreMiddleware(session_maker))
    # Setup sync service
    sync_service = SyncService(
        session_maker, reminder_scheduler, sync_interval=cfg.bot.sync_interval, sync_workers=cfg.bot.sync_workers
    )

    # Start reminder scheduler
    reminder_scheduler_task = asyncio.create_task(reminder_scheduler.start())
    daily_plan_scheduler_task = asyncio.create_task(daily_plan_scheduler.start())
    # Start sync service
    sync_task = asyncio.create_task(sync_service.start_sync_service())

    # Setup middlewares
    setup_middlewares(dp)
    # Include router
    dp.include_router(router)
    # Start bot
    logger.info("Bot is running in polling mode...")
    await dp.start_polling(bot, timeout=cfg.bot.timeout)

    # Stop daily plan scheduler
    stop_daily_plan_scheduler_task = asyncio.create_task(daily_plan_scheduler.stop())
    await asyncio.gather(daily_plan_scheduler_task, stop_daily_plan_scheduler_task)

    # Stop sync service
    stop_task = asyncio.create_task(sync_service.stop())
    await asyncio.gather(sync_task, stop_task)

    # Stop reminder scheduler
    stop_reminder_scheduler_task = asyncio.create_task(reminder_scheduler.stop())
    await asyncio.gather(reminder_scheduler_task, stop_reminder_scheduler_task, stop_daily_plan_scheduler_task)


if __name__ == "__main__":
    asyncio.run(main())
