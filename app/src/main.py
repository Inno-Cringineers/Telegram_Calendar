import asyncio

from aiogram import Bot, Dispatcher
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from config.config import Config, load_config
from database.database import create_engine, create_session_maker, create_tables
from logger.logger import logger, setup_logger
from middlewares.logging_middleware import (
    CallbackQueryLoggingMiddleware,
    MessageLoggingMiddleware,
)
from middlewares.settings_middleware import SettingsMiddleware
from middlewares.store_middlware import StoreMiddleware
from middlewares.whitelist_middleware import WhitelistMiddleware
from router.router import router
from services.daily_plan_scheduler import init_daily_plan_scheduler
from services.metrics_service import MetricsService
from services.reminder_scheduler import init_reminder_scheduler
from services.sync_service import SyncService
from storage.postgres_storage import PostgresStorage
from utils.bot_commands import setup_bot_commands


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


def setup_middlewares(dp: Dispatcher, cfg: Config) -> WhitelistMiddleware | None:
    """Setup all middlewares for dispatcher.

    Args:
        dp: Dispatcher instance.
        cfg: Configuration object.

    Returns:
        WhitelistMiddleware instance if enabled, None otherwise.
    """
    # Logging middlewares
    dp.message.outer_middleware(MessageLoggingMiddleware())
    dp.callback_query.outer_middleware(CallbackQueryLoggingMiddleware())
    # Settings middleware
    dp.message.middleware(SettingsMiddleware())
    dp.callback_query.middleware(SettingsMiddleware())
    # Whitelist middleware (if enabled)
    whitelist_middleware: WhitelistMiddleware | None = None
    if cfg.bot.user_restriction_enabled:
        whitelist_middleware = WhitelistMiddleware(
            whitelist_path=cfg.bot.whitelist_path, enabled=cfg.bot.user_restriction_enabled
        )
        # Whitelist should be checked first (outer middleware)
        dp.message.outer_middleware(whitelist_middleware)
        dp.callback_query.outer_middleware(whitelist_middleware)
        logger.info(f"WhitelistMiddleware enabled with whitelist path: {cfg.bot.whitelist_path}")
    else:
        logger.debug("WhitelistMiddleware disabled")
    logger.debug("Middlewares setup completed")
    return whitelist_middleware


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
    logger.debug(f"Bot sync workers: {cfg.bot.sync_workers}")
    logger.debug(f"Bot sync interval: {cfg.bot.sync_interval}")
    logger.debug(f"Bot metrics interval: {cfg.bot.metrics_interval}")
    logger.debug(f"Settings timezone: {cfg.settings.timezone}")
    logger.debug(f"Settings language: {cfg.settings.language}")
    logger.debug(f"Settings quiet hours enabled: {cfg.settings.quiet_hours_enabled}")
    logger.debug(f"Settings quiet hours start: {cfg.settings.quiet_hours_start}")
    logger.debug(f"Settings quiet hours end: {cfg.settings.quiet_hours_end}")
    logger.debug(f"Settings daily plans enabled: {cfg.settings.daily_plans_enabled}")
    logger.debug(f"Settings daily plans time: {cfg.settings.daily_plans_time}")
    logger.debug(f"Settings default reminder offset: {cfg.settings.default_reminder_offset}")
    logger.debug(f"Bot user restriction enabled: {cfg.bot.user_restriction_enabled}")
    logger.debug(f"Bot whitelist path: {cfg.bot.whitelist_path}")

    # Create bot
    bot = Bot(token=cfg.bot.telegram_token)
    # Setup database
    session_maker = await setup_database_and_store(cfg.database.url)
    # Create dispatcher with PostgreSQL storage
    storage = PostgresStorage(session_maker)
    dp = Dispatcher(storage=storage)
    # Setup reminder scheduler
    reminder_scheduler = init_reminder_scheduler(session_maker, bot)
    daily_plan_scheduler = init_daily_plan_scheduler(session_maker, bot)
    # Setup store middleware
    dp.message.middleware(StoreMiddleware(session_maker))
    dp.callback_query.middleware(StoreMiddleware(session_maker))
    # Setup sync service
    sync_service = SyncService(session_maker, sync_interval=cfg.bot.sync_interval, sync_workers=cfg.bot.sync_workers)
    # Setup metrics service
    metrics_service = MetricsService(session_maker, update_interval=cfg.bot.metrics_interval)

    # Start reminder scheduler
    reminder_scheduler_task = asyncio.create_task(reminder_scheduler.start())
    daily_plan_scheduler_task = asyncio.create_task(daily_plan_scheduler.start())
    # Start sync service
    sync_task = asyncio.create_task(sync_service.start_sync_service())
    # Start metrics service
    metrics_task = asyncio.create_task(metrics_service.start_metrics_service())

    # Setup middlewares
    whitelist_middleware = setup_middlewares(dp, cfg)
    # Start whitelist file watcher if enabled
    if whitelist_middleware:
        await whitelist_middleware.start_file_watcher()

    # Setup bot commands menu
    await setup_bot_commands(bot)

    # Include router
    dp.include_router(router)
    # Start bot
    logger.info("Bot is running in polling mode...")
    await dp.start_polling(bot, timeout=cfg.bot.timeout)

    # Stop whitelist file watcher if enabled
    if whitelist_middleware:
        await whitelist_middleware.stop_file_watcher()

    # Stop daily plan scheduler
    stop_daily_plan_scheduler_task = asyncio.create_task(daily_plan_scheduler.stop())
    await asyncio.gather(daily_plan_scheduler_task, stop_daily_plan_scheduler_task)

    # Stop sync service
    stop_task = asyncio.create_task(sync_service.stop())
    await asyncio.gather(sync_task, stop_task)
    # Wait for services to finish
    stop_metrics_task = asyncio.create_task(metrics_service.stop())
    await asyncio.gather(metrics_task, stop_metrics_task)

    # Stop reminder scheduler
    stop_reminder_scheduler_task = asyncio.create_task(reminder_scheduler.stop())
    await asyncio.gather(reminder_scheduler_task, stop_reminder_scheduler_task, stop_daily_plan_scheduler_task)


if __name__ == "__main__":
    asyncio.run(main())
