"""Reading single WARC records from Common Crawl with HTTP range requests."""

import io

import requests
from warcio.archiveiterator import ArchiveIterator

from news_detector.config import settings
from news_detector.fetch.http import get
from news_detector.models import IndexRecord, WarcPage
from news_detector.utils.logger import get_logger

logger = get_logger(__name__)

PARTIAL_CONTENT = 206


def _charset_from_content_type(content_type: str | None) -> str | None:
    if not content_type:
        return None
    for part in content_type.split(";")[1:]:
        key, _, value = part.strip().partition("=")
        if key.lower() == "charset" and value:
            return value.strip("\"' ").lower()
    return None


def parse_warc_page(data: bytes) -> WarcPage | None:
    """Extract the HTTP response from raw WARC bytes.

    Args:
        data: One gzip-compressed WARC record (or an uncompressed WARC).

    Returns:
        The response body and its declared charset, or ``None`` when the data
        holds no successful ``response`` record.
    """
    for warc_record in ArchiveIterator(io.BytesIO(data)):
        if warc_record.rec_type != "response":
            continue
        http_headers = warc_record.http_headers
        if http_headers is not None and http_headers.get_statuscode() != "200":
            return None
        charset = (
            _charset_from_content_type(http_headers.get_header("Content-Type"))
            if http_headers is not None
            else None
        )
        return WarcPage(body=warc_record.content_stream().read(), charset=charset)
    return None


def fetch_page(session: requests.Session, record: IndexRecord) -> WarcPage | None:
    """Download exactly one WARC record using a byte range.

    Args:
        session: Session created by ``news_detector.http.build_session``.
        record: Index capture pointing at the record.

    Returns:
        The page, or ``None`` when it could not be downloaded or parsed.
    """
    last_byte = record.offset + record.length - 1
    response = get(
        session,
        f"{settings.data_host}/{record.filename}",
        headers={"Range": f"bytes={record.offset}-{last_byte}"},
        expected_status=PARTIAL_CONTENT,
    )
    if response is None:
        return None
    try:
        return parse_warc_page(response.content)
    except requests.RequestException as exc:
        logger.warning("Failed to read WARC body: url=%s error=%s", record.url, exc)
        return None
