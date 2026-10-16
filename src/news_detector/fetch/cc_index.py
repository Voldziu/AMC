"""Querying the Common Crawl CDX index for candidate article URLs."""

import random
import re
import time
from urllib.parse import urlparse

import requests
from pydantic import BaseModel, ValidationError

from news_detector.config import settings
from news_detector.fetch.http import get
from news_detector.models import IndexRecord
from news_detector.utils.logger import get_logger

logger = get_logger(__name__)

# URLs that are certainly not articles (categories, tags, feeds, files).
EXCLUDE = re.compile(
    r"/(tag|tagi|temat|tematy|kategoria|category|autor|author|page|strona|search|szukaj|"
    r"wp-json|feed|rss|login|kontakt|regulamin|polityka)(/|$)|[?#]|\.(jpg|png|pdf|xml|js|css)$",
    re.I,
)
INDEX_FIELDS = "url,filename,offset,length,timestamp,languages"


class _PageCount(BaseModel):
    pages: int = 0


def is_candidate_url(url: str) -> bool:
    """Tell whether a URL looks like an article.

    Args:
        url: Page URL from the index.

    Returns:
        True for long, non-listing, non-file URLs.
    """
    path = urlparse(url).path
    return len(path) >= settings.min_url_path_length and not EXCLUDE.search(url)


def _index_filters() -> list[str]:
    return [
        "status:200",
        "mime-detected:text/html",
        f"languages:{settings.index_language}",
    ]


def _count_pages(session: requests.Session, domain: str) -> int:
    logger.info("%s: asking the index how many pages it has...", domain)
    response = get(
        session,
        settings.index_url,
        params={
            "url": domain,
            "matchType": "domain",
            "output": "json",
            "showNumPages": "true",
        },
    )
    if response is None:
        logger.warning("%s: could not read the page count, domain skipped", domain)
        return 0
    return _PageCount.model_validate_json(response.content).pages


def _fetch_page(session: requests.Session, domain: str, page: int) -> list[IndexRecord]:
    response = get(
        session,
        settings.index_url,
        params={
            "url": domain,
            "matchType": "domain",
            "output": "json",
            "page": str(page),
            "fl": INDEX_FIELDS,
            "filter": _index_filters(),
        },
    )
    if response is None:
        logger.warning("%s: index page %d failed, skipped", domain, page)
        return []
    records: list[IndexRecord] = []
    for line in response.text.splitlines():
        try:
            records.append(IndexRecord.model_validate_json(line))
        except ValidationError:
            logger.debug(
                "Skipping malformed index line: domain=%s page=%d", domain, page
            )
    return records


def find_candidates(
    session: requests.Session, *, domain: str, rng: random.Random
) -> list[IndexRecord]:
    """Sample index pages for a domain and return shuffled candidate captures.

    Args:
        session: Session created by ``news_detector.http.build_session``.
        domain: Domain to look up, including its subdomains.
        rng: Random generator used for page sampling and shuffling.

    Returns:
        Unique captures with article-like URLs, in random order.
    """
    pages = _count_pages(session, domain)
    chosen = rng.sample(range(pages), min(settings.index_pages_per_domain, pages))
    logger.info(
        "%s: index has %d pages, sampling %s (each request may take 10-20 s)",
        domain,
        pages,
        sorted(chosen),
    )
    seen: set[str] = set()
    candidates: list[IndexRecord] = []
    for number, page in enumerate(chosen, start=1):
        started = time.monotonic()
        logger.info(
            "%s: downloading index page %d (%d/%d)...",
            domain,
            page,
            number,
            len(chosen),
        )
        records = _fetch_page(session, domain, page)
        added = 0
        for record in records:
            if record.url not in seen and is_candidate_url(record.url):
                seen.add(record.url)
                candidates.append(record)
                added += 1
        logger.info(
            "%s: index page %d: %d captures, %d article-like URLs, %.1fs",
            domain,
            page,
            len(records),
            added,
            time.monotonic() - started,
        )
        time.sleep(settings.index_delay_seconds)
    rng.shuffle(candidates)
    return candidates
