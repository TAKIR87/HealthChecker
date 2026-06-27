"""
config.py — централизованное чтение конфигурации из переменных окружения.

Все параметры приложения берутся ТОЛЬКО отсюда.
Никаких захардкоженных значений в остальном коде.
"""

import os
from dataclasses import dataclass
from typing import List

from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    """Получить обязательную переменную окружения или упасть с понятной ошибкой."""
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(
            f"Обязательная переменная окружения '{key}' не задана. "
            f"Проверьте файл .env (образец: .env.example)."
        )
    return value


def _parse_urls(raw: str) -> List[str]:
    """Разобрать строку URL через запятую в список, отбросив пустые элементы."""
    return [url.strip() for url in raw.split(",") if url.strip()]


@dataclass(frozen=True)
class AppConfig:
    telegram_bot_token: str
    telegram_chat_id: str
    urls: List[str]
    check_interval_seconds: int = 60
    request_timeout_seconds: int = 10
    log_level: str = "INFO"
    database_path: str = "db.sqlite3"


def load_config() -> AppConfig:
    """Собрать и вернуть конфигурацию приложения."""
    return AppConfig(
        telegram_bot_token=_require("TELEGRAM_BOT_TOKEN"),
        telegram_chat_id=_require("TELEGRAM_CHAT_ID"),
        urls=_parse_urls(_require("URLS")),
        check_interval_seconds=int(os.getenv("CHECK_INTERVAL_SECONDS", "60")),
        request_timeout_seconds=int(os.getenv("REQUEST_TIMEOUT_SECONDS", "10")),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        database_path=os.getenv("DATABASE_PATH", "db.sqlite3"),
    )
