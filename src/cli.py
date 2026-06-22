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

import time

import click

from src.checker import check_url
from src.config import load_config
from src.logger import get_logger, setup_logging
from src.repository import get_latest_results, init_db, save_result

logger = get_logger(__name__)


def _run_single_pass(config) -> None:
    """Выполнить одну проверку всех URL и сохранить результаты в БД."""
    for url in config.urls:
        result = check_url(url, timeout=config.request_timeout_seconds)
        save_result(config.database_path, result)
        if not result.is_up:
            # TODO (Day 3): подключить alert_service.py + notifier.py
            logger.warning("ALERT (not yet sent): {} is DOWN", url)


@click.group()
def cli() -> None:
    """HealthChecker — микросервис мониторинга доступности API-эндпоинтов."""


@cli.command()
def run() -> None:
    """Запустить планировщик: бесконечный цикл проверки URL по расписанию."""
    config = load_config()
    setup_logging(config.log_level)
    init_db(config.database_path)

    logger.info("Starting HealthChecker scheduler...")
    logger.info(
        "Monitoring {} URL(s) every {}s",
        len(config.urls),
        config.check_interval_seconds,
    )
    for url in config.urls:
        logger.info("  → {}", url)

    # NOTE (Day 3): заменить на APScheduler в scheduler.py для гибкого расписания.
    try:
        while True:
            _run_single_pass(config)
            time.sleep(config.check_interval_seconds)
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user.")


@cli.command()
def check() -> None:
    """Разовая немедленная проверка всех URL из конфигурации."""
    config = load_config()
    setup_logging(config.log_level)
    init_db(config.database_path)

    logger.info("Running one-shot check for {} URL(s)...", len(config.urls))
    _run_single_pass(config)
    logger.info("One-shot check complete.")


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
    init_db(config.database_path)

    logger.info("Fetching last {} check results from database...", limit)
    results = get_latest_results(config.database_path, limit=limit)

    if not results:
        click.echo("Нет данных. Запустите 'python -m src.cli check' для первой проверки.")
        return

    for row in results:
        state = "UP  " if row["is_up"] else "DOWN"
        click.echo(
            f"[{row['checked_at']}] {state} | {row['url']} | "
            f"status={row['status_code']} | latency={row['latency_ms']}ms"
        )


if __name__ == "__main__":
    cli()