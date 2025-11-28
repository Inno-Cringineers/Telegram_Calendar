import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

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
    timeout: int
    single_user: bool
    telegram_token: str


@dataclass
class Config:
    logger: LoggerConfig
    database: DatabaseConfig
    bot: BotConfig


def substitute_env_vars(value: Any) -> Any:
    """Recursively substitute environment variables in config values.

    Supports:
    - ${VAR} - simple substitution (empty string if not set)
    - ${VAR:-default} - substitution with default value

    Args:
        value: Config value (can be dict, list, str, or other types).

    Returns:
        Value with environment variables substituted.
    """
    if isinstance(value, dict):
        return {k: substitute_env_vars(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [substitute_env_vars(item) for item in value]
    elif isinstance(value, str):
        # Pattern for ${VAR:-default} or ${VAR}
        # Matches: ${VAR} or ${VAR:-default} or ${VAR:-}
        def replace_var(match: re.Match[str]) -> str:
            var_name = match.group(1)
            default_value = match.group(2) if match.group(2) is not None else None

            env_value = os.getenv(var_name)
            if env_value is not None:
                return env_value
            elif default_value is not None:
                return default_value
            else:
                return ""

        pattern = r"\$\{([^}:]+)(?::-([^}]*))?\}"
        return re.sub(pattern, replace_var, value)
    else:
        return value


def load_yaml_config(config_path: str | None = None) -> dict:
    """Load configuration from YAML file with environment variable substitution.

    Args:
        config_path: Optional path to config file. If None, uses default config.yaml.

    Returns:
        Configuration dictionary with environment variables substituted.
    """
    if config_path is None:
        # Default config path relative to this file
        config_path_obj = Path(__file__).parent / "config.yaml"
    else:
        config_path_obj = Path(config_path)

    if not config_path_obj.exists():
        raise FileNotFoundError(f"Config file not found: {config_path_obj}")

    with open(config_path_obj, encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    # Substitute environment variables
    return substitute_env_vars(config)


def str_to_bool(value: Any) -> bool:
    """Convert string boolean values to bool.

    Args:
        value: Value to convert (can be bool, str, or other types).

    Returns:
        Boolean value.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    return bool(value)


def load_config() -> Config:
    """Load and validate configuration from environment and YAML."""
    # Load YAML config
    yaml_config = load_yaml_config()

    logger_config = LoggerConfig(
        level=yaml_config.get("logger", {}).get("level", "INFO"),
        console=yaml_config.get("logger", {}).get("console", True),
        file_enabled=yaml_config.get("logger", {}).get("file", {}).get("enabled", True),
        file_path=yaml_config.get("logger", {}).get("file", {}).get("path", "logs/bot.log"),
        max_bytes=yaml_config.get("logger", {}).get("file", {}).get("max_bytes", 10485760),
        backup_count=yaml_config.get("logger", {}).get("file", {}).get("backup_count", 5),
    )
    database_config = DatabaseConfig(url=yaml_config.get("database", {}).get("url"))
    bot_config = BotConfig(
        timeout=yaml_config.get("bot", {}).get("timeout", 30),
        single_user=str_to_bool(yaml_config.get("bot", {}).get("single_user", False)),
        telegram_token=yaml_config.get("bot", {}).get("telegram_token"),
    )
    return Config(logger=logger_config, database=database_config, bot=bot_config)
