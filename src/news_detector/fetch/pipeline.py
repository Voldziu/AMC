"""Fetch a sample of Polish news articles from Common Crawl for the domain frame.

Usage:
    uv run python -m news_detector.fetch [--only DOMAIN] [--relaxed]

Everything else (crawl, limits, paths, concurrency) comes from ``config.settings``.
"""

import argparse
import hashlib
import re
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from functools import partial

import pandas as pd
import requests
from tqdm import tqdm

from news_detector.config import settings
from news_detector.fetch.cc_index import find_candidates
from news_detector.fetch.extract import (
    decode_html,
    extract_text,
    has_article_markup,
    parse_pub_date,
)
from news_detector.fetch.http import build_session
from news_detector.fetch.warc import fetch_page
from news_detector.models import Article, IndexRecord, RejectReason
from news_detector.utils.logger import get_logger

logger = get_logger(__name__)

DOMAIN_PATTERN = re.compile(r"^[a-z0-9]([a-z0-9.-]*[a-z0-9])?$")


def _sha1(value: str) -> str:
    return hashlib.sha1(value.encode(), usedforsecurity=False).hexdigest()


def _evaluate(
    session: requests.Session,
    record: IndexRecord,
    *,
    domain: str,
    stratum: str,
    relaxed: bool,
) -> Article | RejectReason:
    page = fetch_page(session, record)
    time.sleep(settings.warc_delay_seconds)
    if page is None:
        return RejectReason.NO_HTML
    html = decode_html(page)
    if not relaxed and not has_article_markup(html):
        return RejectReason.NOT_ARTICLE
    extracted = extract_text(html, url=record.url)
    if extracted is None:
        return RejectReason.NO_TEXT
    if extracted.n_words < settings.min_words:
        return RejectReason.SHORT
    if settings.pub_date_from and settings.pub_date_to:
        published = parse_pub_date(extracted.pub_date)
        if published is None:
            return RejectReason.NO_DATE
        if not settings.pub_date_from <= published <= settings.pub_date_to:
            return RejectReason.WRONG_YEAR
    return Article(
        article_id=_sha1(record.url),
        domain=domain,
        stratum=stratum,
        url=record.url,
        crawl_id=settings.crawl_id,
        warc_filename=record.filename,
        warc_offset=record.offset,
        warc_length=record.length,
        pub_date=extracted.pub_date,
        title=extracted.title,
        crawl_timestamp=record.timestamp,
        author_present=extracted.author_present,
        n_words=extracted.n_words,
        languages=record.languages,
        text_sha1=_sha1(extracted.text),
        text=extracted.text,
    )


def process_record(
    session: requests.Session,
    record: IndexRecord,
    *,
    domain: str,
    stratum: str,
    relaxed: bool,
) -> Article | RejectReason:
    """Download one capture and turn it into an article or a rejection reason.

    Args:
        session: Session created by ``news_detector.http.build_session``.
        record: Index capture to download.
        domain: Domain the capture belongs to.
        stratum: Sampling stratum of the domain.
        relaxed: When true, do not require article markup in the HTML.

    Returns:
        The article, or the reason it was rejected.
    """
    result = _evaluate(session, record, domain=domain, stratum=stratum, relaxed=relaxed)
    if isinstance(result, RejectReason):
        logger.info("Rejected (%s): %s", result.value, record.url)
    else:
        logger.info("Kept (%d words): %s", result.n_words, record.url)
    return result


def run_domain(
    session: requests.Session,
    *,
    domain: str,
    stratum: str,
    candidates: list[IndexRecord],
    relaxed: bool,
) -> None:
    """Fetch articles for one domain and write them to a JSONL file.

    Args:
        session: Session created by ``news_detector.http.build_session``.
        domain: Domain to sample.
        stratum: Sampling stratum of the domain.
        candidates: Captures from the index, in the order to try them.
        relaxed: When true, do not require article markup in the HTML.
    """
    to_fetch = candidates[: settings.max_fetch_per_domain]
    if not to_fetch:
        logger.warning("%s: no article candidates found in the index", domain)
    else:
        logger.info(
            "%s: fetching up to %d of %d candidates from WARC files (%d workers)",
            domain,
            len(to_fetch),
            len(candidates),
            settings.workers,
        )
    worker = partial(
        process_record, session, domain=domain, stratum=stratum, relaxed=relaxed
    )
    kept: list[Article] = []
    rejects: Counter[RejectReason] = Counter()
    seen_hashes: set[str] = set()

    with (
        ThreadPoolExecutor(max_workers=settings.workers) as executor,
        tqdm(
            total=settings.articles_per_domain,
            desc=f"  {domain}",
            unit="art",
            position=1,
            leave=False,
        ) as bar,
    ):
        for start in range(0, len(to_fetch), settings.workers):
            if len(kept) >= settings.articles_per_domain:
                break
            batch = to_fetch[start : start + settings.workers]
            for result in executor.map(worker, batch):
                if len(kept) >= settings.articles_per_domain:
                    break
                if isinstance(result, RejectReason):
                    rejects[result] += 1
                elif result.text_sha1 in seen_hashes:
                    rejects[RejectReason.DUPLICATE] += 1
                    logger.info("Rejected (duplicate): %s", result.url)
                else:
                    seen_hashes.add(result.text_sha1)
                    kept.append(result)
                    bar.update(1)
                bar.set_postfix(rejected=sum(rejects.values()))

    settings.raw_dir.mkdir(parents=True, exist_ok=True)
    with (settings.raw_dir / f"{domain}.jsonl").open("w", encoding="utf-8") as file:
        for article in kept:
            file.write(article.model_dump_json() + "\n")
    logger.info(
        "%-35s %s candidates=%5d kept=%3d rejected=%s",
        domain,
        stratum,
        len(candidates),
        len(kept),
        {reason.value: count for reason, count in rejects.items()},
    )


def rebuild_meta() -> None:
    """Write the public metadata CSV (without text) from all JSONL files."""
    rows: list[dict[str, object]] = []
    for path in sorted(settings.raw_dir.glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                article = Article.model_validate_json(line)
                rows.append(article.model_dump(exclude={"text"}))
    settings.derived_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(settings.meta_csv, index=False)
    logger.info("Saved %s (%d rows)", settings.meta_csv, len(rows))


def main() -> None:
    """Run the fetch pipeline for every news domain in the frame."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", default=None, help="process only this domain (test)")
    parser.add_argument(
        "--relaxed", action="store_true", help="do not require article markup"
    )
    args = parser.parse_args()

    frame = pd.read_csv(settings.domains_csv)
    if args.only:
        frame = frame[frame["domain"] == args.only]

    todo: list[tuple[str, str]] = []
    for raw_domain, raw_stratum in zip(frame["domain"], frame["stratum"], strict=True):
        domain, stratum = str(raw_domain).strip().lower(), str(raw_stratum)
        if not DOMAIN_PATTERN.match(domain):
            logger.warning("Skipping invalid domain name: %r", domain)
        elif (settings.raw_dir / f"{domain}.jsonl").exists():
            logger.info("%s: skipping (already fetched)", domain)
        else:
            todo.append((domain, stratum))

    if todo:
        session = build_session()
        candidates = find_candidates(session, [domain for domain, _ in todo])
        with tqdm(todo, desc="Domains", unit="dom", position=0) as domain_bar:
            for domain, stratum in domain_bar:
                domain_bar.set_postfix_str(domain)
                run_domain(
                    session,
                    domain=domain,
                    stratum=stratum,
                    candidates=candidates[domain],
                    relaxed=args.relaxed,
                )
    rebuild_meta()


if __name__ == "__main__":
    main()
