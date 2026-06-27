"""
logger.py — настройка единой системы логирования на базе Loguru.

Логи пишутся одновременно:
  - в консоль (для Docker / разработки)
  - в ротируемый файл logs/healthchecker.log (ротация 10 MB, хранение 7 дней)

Использование в других модулях:
    from src.logger import get_logger
    logger = get_logger(__name__)
    logger.info("Сообщение")
    logger.error("Ошибка: {err}", err=e)
"""

import sys
from pathlib import Path

from loguru import logger as _loguru_logger

_configured = False


def setup_logging(log_level: str = "INFO") -> None:
    """
    Инициализировать логирование. Вызывать один раз при старте приложения.

    Args:
        log_level: уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    global _configured
    if _configured:
        return

    _loguru_logger.remove()

    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    # Консоль — для Docker и живого наблюдения
    _loguru_logger.add(
        sys.stdout,
        level=log_level,
        format=log_format,
        colorize=True,
    )

    # Файл — с ротацией по размеру и автоочисткой
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    _loguru_logger.add(
        logs_dir / "healthchecker.log",
        level=log_level,
        format=log_format,
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        encoding="utf-8",
        colorize=False,
    )

    _configured = True
    _loguru_logger.info("Logging initialized. Level: {}", log_level)


def get_logger(name: str):
    """
    Получить логгер с привязкой к имени модуля.

    Args:
        name: имя модуля, обычно передаётся как __name__.

    Returns:
        Объект логгера Loguru с контекстом name.
    """
    return _loguru_logger.bind(name=name)
