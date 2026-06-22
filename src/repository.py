"""
repository.py — слой доступа к данным (SQLite).

Отвечает за создание схемы БД, сохранение результатов проверок
и чтение истории. Никакой бизнес-логики — только хранение.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, List

from src.checker import CheckResult
from src.logger import get_logger

logger = get_logger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS check_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL,
    is_up INTEGER NOT NULL,
    status_code INTEGER,
    latency_ms INTEGER,
    ssl_valid INTEGER,
    ssl_days_left INTEGER,
    error TEXT,
    checked_at TEXT NOT NULL
);
"""


@contextmanager
def _connect(db_path: str) -> Iterator[sqlite3.Connection]:
    """Контекстный менеджер для подключения к SQLite с автозакрытием."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        yield conn
    finally:
        conn.close()


def init_db(db_path: str) -> None:
    """Создать таблицу check_results, если она ещё не существует."""
    with _connect(db_path) as conn:
        conn.execute(_SCHEMA)
        conn.commit()
    logger.info("Database initialized at {}", db_path)


def save_result(db_path: str, result: CheckResult) -> None:
    """Сохранить один результат проверки в БД."""
    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO check_results
                (url, is_up, status_code, latency_ms, ssl_valid, ssl_days_left, error, checked_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result.url,
                int(result.is_up),
                result.status_code,
                result.latency_ms,
                None if result.ssl_valid is None else int(result.ssl_valid),
                result.ssl_days_left,
                result.error,
                result.checked_at,
            ),
        )
        conn.commit()


def get_latest_results(db_path: str, limit: int = 10) -> List[dict]:
    """
    Получить последние N результатов проверок, отсортированные по времени.

    Returns:
        Список словарей с данными о каждой проверке.
    """
    with _connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            "SELECT * FROM check_results ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        return [dict(row) for row in cursor.fetchall()]