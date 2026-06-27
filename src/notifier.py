"""
notifier.py — инфраструктурный слой отправки уведомлений в Telegram.

Отвечает только за факт отправки сообщения через Bot API.
Никакой бизнес-логики о том, "когда" слать — это alert_service.py.
"""

import httpx

from src.logger import get_logger

logger = get_logger(__name__)

_TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"


def send_telegram_message(bot_token: str, chat_id: str, text: str, timeout: int = 10) -> bool:
    """
    Отправить текстовое сообщение в Telegram-чат.

    Args:
        bot_token: токен бота из .env (TELEGRAM_BOT_TOKEN).
        chat_id: ID чата/канала из .env (TELEGRAM_CHAT_ID).
        text: текст сообщения.
        timeout: таймаут запроса в секундах.

    Returns:
        True, если сообщение отправлено успешно, иначе False.
    """
    url = _TELEGRAM_API_URL.format(token=bot_token)
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
    }

    try:
        response = httpx.post(url, json=payload, timeout=timeout)
        response.raise_for_status()
        logger.info("Telegram alert sent successfully.")
        return True

    except httpx.HTTPStatusError as e:
        logger.error(
            "Telegram API returned an error: {} | {}",
            e.response.status_code,
            e.response.text,
        )
        return False

    except httpx.RequestError as e:
        logger.error("Failed to reach Telegram API: {}", str(e))
        return False
