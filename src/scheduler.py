"""
scheduler.py — планировщик периодических проверок на базе APScheduler.

Заменяет наивный цикл time.sleep() на полноценный BlockingScheduler,
что даёт более предсказуемые интервалы (не "интервал + время работы",
а строго фиксированный интервал) и более чистое завершение по Ctrl+C.
"""

from datetime import datetime, timezone

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.events import EVENT_JOB_ERROR

from src.logger import get_logger

logger = get_logger(__name__)


def _on_job_error(event) -> None:
    """Залогировать необработанное исключение внутри запланированной задачи."""
    logger.error("Scheduled job raised an exception: {}", event.exception)


def start_scheduler(job_fn, interval_seconds: int) -> None:
    """
    Запустить блокирующий планировщик, выполняющий job_fn каждые interval_seconds.

    Первый запуск происходит немедленно, затем — строго через заданный интервал.

    Args:
        job_fn: функция без аргументов, выполняющая один проход проверок.
        interval_seconds: интервал между запусками в секундах.
    """
    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_listener(_on_job_error, EVENT_JOB_ERROR)

    scheduler.add_job(
        job_fn,
        trigger="interval",
        seconds=interval_seconds,
        next_run_time=datetime.now(timezone.utc),  # запустить немедленно при старте
        id="health_check_job",
        max_instances=1,  # не дать задачам накладываться друг на друга
        coalesce=True,
    )

    logger.info("Scheduler configured. Interval: {}s. Starting...", interval_seconds)

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped by user.")
        scheduler.shutdown(wait=False)