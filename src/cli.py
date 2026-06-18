"""
cli.py — точка входа в приложение, CLI-интерфейс на базе Click.

Команды:
    run     — запустить планировщик (бесконечный цикл мониторинга)
    check   — выполнить разовую проверку всех URL прямо сейчас
    status  — вывести последние результаты проверок из базы данных

Запуск:
    python -m src.cli run
    python -m src.cli check
    python -m src.cli status --limit 20
"""

import click

from src.config import load_config
from src.logger import get_logger, setup_logging

logger = get_logger(__name__)


@click.group()
def cli() -> None:
    """HealthChecker — микросервис мониторинга доступности API-эндпоинтов."""


@cli.command()
def run() -> None:
    """Запустить планировщик: бесконечный цикл проверки URL по расписанию."""
    config = load_config()
    setup_logging(config.log_level)

    logger.info("Starting HealthChecker scheduler...")
    logger.info(
        "Monitoring {} URL(s) every {}s",
        len(config.urls),
        config.check_interval_seconds,
    )
    for url in config.urls:
        logger.info("  → {}", url)

    # TODO (Day 2): инициализировать БД, запустить scheduler.py
    logger.warning("Scheduler not yet implemented — coming in Day 2.")


@cli.command()
def check() -> None:
    """Разовая немедленная проверка всех URL из конфигурации."""
    config = load_config()
    setup_logging(config.log_level)

    logger.info("Running one-shot check for {} URL(s)...", len(config.urls))

    # TODO (Day 2): вызвать checker.py для каждого URL
    for url in config.urls:
        logger.info("  [TODO] Checking: {}", url)

    logger.warning("Checker not yet implemented — coming in Day 2.")


@cli.command()
@click.option(
    "--limit",
    default=10,
    show_default=True,
    help="Количество последних результатов для отображения.",
)
def status(limit: int) -> None:
    """Показать последние N результатов проверок из базы данных."""
    config = load_config()
    setup_logging(config.log_level)

    logger.info("Fetching last {} check results from database...", limit)

    # TODO (Day 2): вызвать repository.py и вывести результаты
    logger.warning("Repository not yet implemented — coming in Day 2.")


if __name__ == "__main__":
    cli()