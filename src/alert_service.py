"""
alert_service.py — бизнес-логика принятия решения об отправке алерта.

Ключевая идея: алерт шлётся не на КАЖДУЮ неудачную проверку, а только
при ИЗМЕНЕНИИ состояния сервиса (UP → DOWN или DOWN → UP). Это защищает
от спама в Telegram, если сервис лежит долго.

Дополнительно: отдельный алерт, если SSL-сертификат истекает
в ближайшие SSL_WARNING_THRESHOLD_DAYS дней.
"""

from typing import Dict

from src.checker import CheckResult
from src.logger import get_logger
from src.notifier import send_telegram_message

logger = get_logger(__name__)

SSL_WARNING_THRESHOLD_DAYS = 14

# Хранит последнее известное состояние (is_up) для каждого URL в рамках процесса.
# Простое решение для индивидуального проекта; при горизонтальном масштабировании
# это должно переехать в БД/Redis.
_last_known_state: Dict[str, bool] = {}

# Чтобы не слать предупреждение об SSL на каждом цикле — шлём один раз за процесс.
_ssl_warning_sent: Dict[str, bool] = {}


def evaluate_and_alert(result: CheckResult, bot_token: str, chat_id: str) -> None:
    """
    Проанализировать результат проверки и отправить алерт при необходимости.

    Алерт отправляется в двух случаях:
      1. Смена состояния сервиса (восстановился / упал).
      2. SSL-сертификат скоро истекает (предупреждение один раз).

    Args:
        result: результат последней проверки URL.
        bot_token: токен Telegram-бота.
        chat_id: ID чата для отправки.
    """
    _check_state_change(result, bot_token, chat_id)
    _check_ssl_expiry(result, bot_token, chat_id)


def _check_state_change(result: CheckResult, bot_token: str, chat_id: str) -> None:
    previous_state = _last_known_state.get(result.url)

    # Первая проверка этого URL за время работы процесса — просто запомнить состояние.
    if previous_state is None:
        _last_known_state[result.url] = result.is_up
        return

    # Состояние не изменилось — алерт не нужен.
    if previous_state == result.is_up:
        return

    _last_known_state[result.url] = result.is_up

    if not result.is_up:
        message = (
            f"🔴 <b>СЕРВИС НЕДОСТУПЕН</b>\n"
            f"URL: {result.url}\n"
            f"Код ответа: {result.status_code or '—'}\n"
            f"Ошибка: {result.error or 'не указана'}\n"
            f"Время: {result.checked_at}"
        )
        logger.warning("State change DOWN for {}. Sending alert.", result.url)
    else:
        message = (
            f"🟢 <b>СЕРВИС ВОССТАНОВЛЕН</b>\n"
            f"URL: {result.url}\n"
            f"Время отклика: {result.latency_ms}ms\n"
            f"Время: {result.checked_at}"
        )
        logger.info("State change UP (recovered) for {}. Sending alert.", result.url)

    send_telegram_message(bot_token, chat_id, message)


def _check_ssl_expiry(result: CheckResult, bot_token: str, chat_id: str) -> None:
    if result.ssl_days_left is None or result.ssl_valid is False:
        return

    if result.ssl_days_left > SSL_WARNING_THRESHOLD_DAYS:
        return

    if _ssl_warning_sent.get(result.url):
        return

    message = (
        f"⚠️ <b>SSL-СЕРТИФИКАТ СКОРО ИСТЕКАЕТ</b>\n"
        f"URL: {result.url}\n"
        f"Осталось дней: {result.ssl_days_left}\n"
        f"Время: {result.checked_at}"
    )
    logger.warning("SSL expiry warning for {}: {} days left.", result.url, result.ssl_days_left)

    if send_telegram_message(bot_token, chat_id, message):
        _ssl_warning_sent[result.url] = True