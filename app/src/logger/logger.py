import logging
import logging.handlers
import time
from pathlib import Path

from config.config import LoggerConfig

# Будет инициализирован в setup_logger()
logger = logging.getLogger("telegram_calendar_bot")


def setup_logger(logger_config: LoggerConfig) -> logging.Logger:
    """
    Configure logger based on config settings.

    Args:
        logger_config: LoggerConfig object with logger settings
    """
    global logger

    logger.setLevel(getattr(logging, logger_config.level.upper(), logging.INFO))

    # Clear existing handlers
    logger.handlers.clear()

    # Create logs directory
    if logger_config.file_enabled:
        log_dir = Path(logger_config.file_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)

    # Formatter
    if logger_config.level.upper() == "DEBUG":
        format_string = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
    else:
        format_string = "%(asctime)s - %(levelname)s - %(message)s"

    # Use local timezone for logging
    # When Docker volumes /etc/localtime and /etc/timezone are mounted,
    # time.localtime will use the host machine's timezone
    formatter = logging.Formatter(
        format_string,
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    # Explicitly set converter to use local time (not UTC)
    # This ensures logs show time according to host machine's timezone
    # when /etc/localtime is mounted in Docker
    formatter.converter = time.localtime

    # Console handler - always enabled
    if logger_config.console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, logger_config.level.upper(), logging.INFO))
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler
    if logger_config.file_enabled:
        file_handler = logging.handlers.RotatingFileHandler(
            logger_config.file_path,
            maxBytes=logger_config.max_bytes,
            backupCount=logger_config.backup_count,
        )
        file_handler.setLevel(logging.DEBUG)  # Файл логирует все
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Suppress verbose library logs
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)

    return logger
