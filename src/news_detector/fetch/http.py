"""HTTP client with connection reuse and retries that honour ``Retry-After``."""

import time
from collections.abc import Mapping
from types import TracebackType
from typing import Self

import requests
from requests.adapters import HTTPAdapter
from urllib3.connectionpool import ConnectionPool
from urllib3.response import BaseHTTPResponse
from urllib3.util.retry import Retry

from news_detector.config import settings
from news_detector.utils.logger import get_logger

logger = get_logger(__name__)

RETRY_STATUSES = (429, 500, 502, 503, 504)


class _LoggingRetry(Retry):
    """``Retry`` that reports every retry together with the wait before it."""

    def increment(
        self,
        method: str | None = None,
        url: str | None = None,
        response: BaseHTTPResponse | None = None,
        error: Exception | None = None,
        _pool: ConnectionPool | None = None,
        _stacktrace: TracebackType | None = None,
    ) -> Self:
        new = super().increment(method, url, response, error, _pool, _stacktrace)
        reason = f"status {response.status}" if response else repr(error)
        logger.warning(
            "Retry %d/%d in %.0fs (%s): %s",
            settings.max_retries - (new.total or 0),
            settings.max_retries,
            new.get_backoff_time(),
            reason,
            url,
        )
        return new


def build_session() -> requests.Session:
    """Create a session with the project User-Agent and a retry policy.

    Returns:
        A ``requests.Session`` sized for ``settings.workers`` parallel threads.
    """
    retry = _LoggingRetry(
        total=settings.max_retries,
        backoff_factor=settings.retry_backoff_seconds,
        status_forcelist=RETRY_STATUSES,
        allowed_methods=("GET",),
        respect_retry_after_header=True,
        raise_on_status=False,
    )
    adapter = HTTPAdapter(
        max_retries=retry,
        pool_connections=settings.workers,
        pool_maxsize=settings.workers,
    )
    session = requests.Session()
    session.headers["User-Agent"] = settings.user_agent
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def get(
    session: requests.Session,
    url: str,
    *,
    params: Mapping[str, str | list[str]] | None = None,
    headers: Mapping[str, str] | None = None,
    expected_status: int = 200,
) -> requests.Response | None:
    """Perform a GET request.

    The body is streamed, so a response with an unexpected status (for example a
    server ignoring ``Range`` and sending a whole WARC file) is never downloaded.

    Args:
        session: Session created by ``build_session``.
        url: Target URL.
        params: Optional query parameters.
        headers: Optional extra request headers.
        expected_status: The only status code treated as success.

    Returns:
        The response, or ``None`` when the request failed or the status differed.
    """
    started = time.monotonic()
    try:
        response = session.get(
            url,
            params=params,
            headers=headers,
            timeout=settings.request_timeout_seconds,
            stream=True,
        )
    except requests.RequestException as exc:
        logger.warning("Request failed: url=%s error=%s", url, exc)
        return None
    logger.debug(
        "GET %s -> %d in %.1fs",
        response.url,
        response.status_code,
        time.monotonic() - started,
    )
    if response.status_code != expected_status:
        logger.warning(
            "Unexpected status: url=%s status=%d expected=%d",
            url,
            response.status_code,
            expected_status,
        )
        response.close()
        return None
    return response
