import logging
import logging.handlers
import os
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

    formatter = logging.Formatter(
        format_string,
        datefmt="%Y-%m-%d %H:%M:%S",
    )

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

    # Setup OpenTelemetry logging handler for Grafana Cloud
    _setup_otel_logging(logger, logger_config)

    return logger


def _setup_otel_logging(logger: logging.Logger, logger_config: LoggerConfig) -> None:
    """
    Setup OpenTelemetry logging handler to send logs to Grafana Cloud.

    Args:
        logger: Logger instance to add OpenTelemetry handler to.
        logger_config: Logger configuration.
    """
    # Only setup if OTLP endpoint is configured
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not otlp_endpoint:
        logger.debug("OpenTelemetry OTLP endpoint not configured, skipping log export")
        return

    try:
        from opentelemetry._logs import set_logger_provider
        from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
        from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
        from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter

        # Create logger provider
        logger_provider = LoggerProvider()
        set_logger_provider(logger_provider)

        # Create OTLP exporter
        otlp_exporter = OTLPLogExporter()
        logger_provider.add_log_record_processor(BatchLogRecordProcessor(otlp_exporter))

        # Create and add OpenTelemetry handler
        otel_handler = LoggingHandler(logger_provider=logger_provider)
        # Use the same level as console handler
        otel_handler.setLevel(
            getattr(logging, logger_config.level.upper(), logging.INFO)
        )
        logger.addHandler(otel_handler)

        logger.debug("OpenTelemetry logging handler configured successfully")
    except ImportError as e:
        logger.warning(
            f"OpenTelemetry logging packages not available: {e}. "
            "Logs will not be sent to Grafana Cloud."
        )
    except Exception as e:
        logger.warning(
            f"Failed to setup OpenTelemetry logging: {e}. "
            "Logs will not be sent to Grafana Cloud."
        )
