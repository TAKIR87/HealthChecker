"""
checker.py — бизнес-логика проверки доступности одного URL.

Отвечает за:
  - HTTP-запрос и замер времени отклика
  - Проверку валидности и срока действия SSL-сертификата
  - Формирование структурированного результата CheckResult
"""

import ssl
import socket
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse

import httpx

from src.logger import get_logger

logger = get_logger(__name__)


@dataclass
class CheckResult:
    url: str
    is_up: bool
    status_code: Optional[int]
    latency_ms: Optional[int]
    ssl_valid: Optional[bool]
    ssl_days_left: Optional[int]
    error: Optional[str]
    checked_at: str


def _check_ssl_certificate(hostname: str, timeout: int) -> tuple[Optional[bool], Optional[int]]:
    """
    Проверить SSL-сертификат хоста и количество дней до истечения.

    Returns:
        (валиден_ли_сертификат, дней_до_истечения) либо (None, None), если не HTTPS.
    """
    try:
        context = ssl.create_default_context()
        with socket.create_connection((hostname, 443), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()

        expires_at = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
        expires_at = expires_at.replace(tzinfo=timezone.utc)
        days_left = (expires_at - datetime.now(timezone.utc)).days
        return True, days_left

    except ssl.SSLCertVerificationError as e:
        logger.warning("SSL verification failed for {}: {}", hostname, e)
        return False, None
    except (socket.timeout, socket.gaierror, ConnectionRefusedError, OSError) as e:
        logger.debug("SSL check skipped for {} (connection issue: {})", hostname, e)
        return None, None


def check_url(url: str, timeout: int = 10) -> CheckResult:
    """
    Выполнить полную проверку одного URL: доступность + SSL.

    Args:
        url: адрес для проверки.
        timeout: таймаут запроса в секундах.

    Returns:
        CheckResult с полной информацией о состоянии сервиса.
    """
    checked_at = datetime.now(timezone.utc).isoformat()
    parsed = urlparse(url)
    is_https = parsed.scheme == "https"

    ssl_valid, ssl_days_left = (None, None)

    try:
        start = time.monotonic()
        response = httpx.get(url, timeout=timeout, follow_redirects=True)
        latency_ms = int((time.monotonic() - start) * 1000)

        is_up = response.status_code < 500

        if is_https:
            ssl_valid, ssl_days_left = _check_ssl_certificate(parsed.hostname, timeout)

        logger.info(
            "{} | {} | {}ms{}",
            "OK" if is_up else "FAIL",
            url,
            latency_ms,
            f" | SSL valid ({ssl_days_left}d)" if ssl_valid else "",
        )

        return CheckResult(
            url=url,
            is_up=is_up,
            status_code=response.status_code,
            latency_ms=latency_ms,
            ssl_valid=ssl_valid,
            ssl_days_left=ssl_days_left,
            error=None,
            checked_at=checked_at,
        )

    except httpx.RequestError as e:
        logger.error("FAIL | {} | {}", url, str(e))
        return CheckResult(
            url=url,
            is_up=False,
            status_code=None,
            latency_ms=None,
            ssl_valid=None,
            ssl_days_left=None,
            error=str(e),
            checked_at=checked_at,
        )
