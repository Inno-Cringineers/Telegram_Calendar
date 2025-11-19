import os
from dataclasses import dataclass
from pathlib import Path

import yaml

# TODO: REFINE config


@dataclass
class LoggerConfig:
    level: str
    console: bool
    file_enabled: bool
    file_path: str
    max_bytes: int
    backup_count: int


@dataclass
class DatabaseConfig:
    url: str


@dataclass
class BotConfig:
    polling_enabled: bool
    timeout: int


@dataclass
class Config:
    telegram_token: str
    db_url: str
    logger: LoggerConfig
    database: DatabaseConfig
    bot: BotConfig


def load_yaml_config(config_path: str | None = None) -> dict:
    """Load configuration from YAML file."""
    if config_path is None:
        # Default config path relative to this file
        config_path_obj = Path(__file__).parent.parent / "config.yaml"
    else:
        config_path_obj = Path(config_path)

    if not config_path_obj.exists():
        raise FileNotFoundError(f"Config file not found: {config_path_obj}")

    with open(config_path_obj, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_config() -> Config:
    """Load and validate configuration from environment and YAML."""
    # Load YAML config
    yaml_config = load_yaml_config()

    # Get from environment - required
    telegram_token = os.getenv("TELEGRAM_TOKEN")
    if not telegram_token:
        raise ValueError("TELEGRAM_TOKEN environment variable is not set")

    # DB_URL from environment - required
    db_url = os.getenv("DB_URL")
    if not db_url:
        raise ValueError("DB_URL environment variable is not set")

    # Logger config
    logger_cfg = yaml_config.get("logger", {})
    logger_config = LoggerConfig(
        level=logger_cfg.get("level", "INFO"),
        console=logger_cfg.get("console", True),
        file_enabled=logger_cfg.get("file", {}).get("enabled", True),
        file_path=logger_cfg.get("file", {}).get("path", "logs/bot.log"),
        max_bytes=logger_cfg.get("file", {}).get("max_bytes", 10485760),
        backup_count=logger_cfg.get("file", {}).get("backup_count", 5),
    )

    # Database config
    database_config = DatabaseConfig(url=db_url)

    # Bot config
    bot_cfg = yaml_config.get("bot", {})
    bot_config = BotConfig(
        polling_enabled=bot_cfg.get("polling_enabled", True),
        timeout=bot_cfg.get("timeout", 30),
    )

    return Config(
        telegram_token=telegram_token,
        db_url=db_url,
        logger=logger_config,
        database=database_config,
        bot=bot_config,
    )
