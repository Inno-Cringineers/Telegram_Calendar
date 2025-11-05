import os
from dataclasses import dataclass

@dataclass
class Config:
    telegram_token: str

def load_config() -> Config:
    telegram_token = os.getenv("TELEGRAM_TOKEN")
    if not telegram_token:
        raise ValueError("TELEGRAM_TOKEN environment variable is not set")
    
    return Config(telegram_token=telegram_token)