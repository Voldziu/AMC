"""Fetch a sample of Polish news articles from Common Crawl for the domain frame.

Usage:
    uv run python -m news_detector.fetch [--only DOMAIN] [--year YEAR]
                                         [--relaxed] [--retry-incomplete]

The years and the crawl each of them is taken from are listed in the YAML file
``settings.crawls_file``. Years are processed one after another; for a year only
articles published in that year are kept. Everything else (limits, paths,
concurrency) comes from ``config.settings``.

Progress is saved as it goes (see ``news_detector.fetch.store``), so a killed run
resumes where it stopped. Domains that finished below the quota are left alone
unless ``--retry-incomplete`` is given; they then continue with candidates not
tried before (raise ``MAX_FETCH_PER_DOMAIN`` to get more of them).
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

from news_detector.config import CrawlMapError, settings
from news_detector.fetch.cc_index import find_candidates
from news_detector.fetch.extract import (
    decode_html,
    extract_text,
    has_article_markup,
    parse_pub_date,
)
from news_detector.fetch.http import build_session
from news_detector.fetch.store import DomainStatus, DomainStore, read_articles
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
    year: int,
    crawl_id: str,
    relaxed: bool,
) -> Article | RejectReason:
    page = fetch_page(session, record)
    time.sleep(settings.warc_delay_seconds)
    if page is None:
        return RejectReason.NO_HTML
    html = decode_html(page)
    if (
        not relaxed
        and domain not in settings.relaxed_domains
        and not has_article_markup(html)
    ):
        return RejectReason.NOT_ARTICLE
    extracted = extract_text(html, url=record.url)
    if extracted is None:
        return RejectReason.NO_TEXT
    if extracted.n_words < settings.min_words:
        return RejectReason.SHORT
    published = parse_pub_date(extracted.pub_date)
    if published is None:
        return RejectReason.NO_DATE
    if published.year != year:
        return RejectReason.WRONG_YEAR
    return Article(
        article_id=_sha1(record.url),
        domain=domain,
        stratum=stratum,
        url=record.url,
        crawl_id=crawl_id,
        warc_filename=record.filename,
        warc_offset=record.offset,
        warc_length=record.length,
        pub_date=extracted.pub_date,
        pub_year=published.year,
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
    year: int,
    crawl_id: str,
    relaxed: bool,
) -> Article | RejectReason:
    """Download one capture and turn it into an article or a rejection reason.

    Args:
        session: Session created by ``news_detector.http.build_session``.
        record: Index capture to download.
        domain: Domain the capture belongs to.
        stratum: Sampling stratum of the domain.
        year: Publication year being collected; other years are rejected.
        crawl_id: Crawl the capture comes from.
        relaxed: When true, do not require article markup in the HTML.

    Returns:
        The article, or the reason it was rejected.
    """
    result = _evaluate(
        session,
        record,
        domain=domain,
        stratum=stratum,
        year=year,
        crawl_id=crawl_id,
        relaxed=relaxed,
    )
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
    year: int,
    crawl_id: str,
    candidates: list[IndexRecord],
    relaxed: bool,
) -> None:
    """Collect one year of articles for one domain, saving each one as it is kept.

    Candidates that an earlier run already downloaded are skipped, so an
    interrupted or incomplete domain continues where it stopped.

    Args:
        session: Session created by ``news_detector.http.build_session``.
        domain: Domain to sample.
        stratum: Sampling stratum of the domain.
        year: Publication year to collect.
        crawl_id: Crawl the candidates come from.
        candidates: Captures from the index, in the order to try them.
        relaxed: When true, do not require article markup in the HTML.
    """
    quota = settings.articles_per_domain_year
    store = DomainStore(year, domain)
    kept, tried = store.start()
    seen_hashes = {article.text_sha1 for article in kept}
    to_fetch = candidates[: settings.max_fetch_per_domain]
    pending = [record for record in to_fetch if record.url not in tried]

    if not to_fetch:
        logger.warning("%s %d: no article candidates in %s", domain, year, crawl_id)
    else:
        logger.info(
            "%s %d: %d kept so far, %d of %d candidates left to fetch (%d workers)",
            domain,
            year,
            len(kept),
            len(pending),
            len(to_fetch),
            settings.workers,
        )
    worker = partial(
        process_record,
        session,
        domain=domain,
        stratum=stratum,
        year=year,
        crawl_id=crawl_id,
        relaxed=relaxed,
    )
    rejects: Counter[RejectReason] = Counter()

    with (
        ThreadPoolExecutor(max_workers=settings.workers) as executor,
        tqdm(
            total=quota,
            initial=len(kept),
            desc=f"  {domain}",
            unit="art",
            position=1,
            leave=False,
        ) as bar,
    ):
        for start in range(0, len(pending), settings.workers):
            if len(kept) >= quota:
                break
            batch = pending[start : start + settings.workers]
            for record, result in zip(batch, executor.map(worker, batch), strict=True):
                if len(kept) >= quota:
                    break
                if isinstance(result, RejectReason):
                    rejects[result] += 1
                elif result.text_sha1 in seen_hashes:
                    rejects[RejectReason.DUPLICATE] += 1
                    logger.info("Rejected (duplicate): %s", result.url)
                else:
                    seen_hashes.add(result.text_sha1)
                    kept.append(result)
                    store.add_article(result)
                    bar.update(1)
                store.add_tried(record.url)
                tried.add(record.url)
                bar.set_postfix(rejected=sum(rejects.values()))

    store.finish(kept=len(kept), tried=len(tried), candidates=len(candidates))
    logger.info(
        "%-30s %d %s candidates=%5d kept=%3d/%d rejected=%s",
        domain,
        year,
        stratum,
        len(candidates),
        len(kept),
        quota,
        {reason.value: count for reason, count in rejects.items()},
    )
    if len(kept) < quota:
        logger.warning(
            "%s %d: only %d of %d articles found (%d candidates tried); "
            "raise MAX_FETCH_PER_DOMAIN and rerun with --retry-incomplete to continue",
            domain,
            year,
            len(kept),
            quota,
            len(tried),
        )


def rebuild_meta() -> None:
    """Write the public metadata CSV (without text) from all JSONL files."""
    rows: list[dict[str, object]] = []
    for year in settings.crawl_map:
        for path in sorted(settings.raw_dir(year).glob("*.jsonl")):
            rows.extend(
                article.model_dump(exclude={"text"}) for article in read_articles(path)
            )
    settings.derived_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(settings.meta_csv, index=False)
    logger.info("Saved %s (%d rows)", settings.meta_csv, len(rows))


def _load_domains(only: str | None) -> list[tuple[str, str]]:
    """Read valid (domain, stratum) pairs from the sampling frame."""
    frame = pd.read_csv(settings.domains_csv)
    if only:
        frame = frame[frame["domain"] == only]
    domains: list[tuple[str, str]] = []
    for raw_domain, raw_stratum in zip(frame["domain"], frame["stratum"], strict=True):
        domain, stratum = str(raw_domain).strip().lower(), str(raw_stratum)
        if DOMAIN_PATTERN.match(domain):
            domains.append((domain, stratum))
        else:
            logger.warning("Skipping invalid domain name: %r", domain)
    return domains


def _select_todo(
    year: int, domains: list[tuple[str, str]], *, retry_incomplete: bool
) -> list[tuple[str, str]]:
    """Pick the domains that still need work for a year and log why."""
    wanted = {DomainStatus.NEW, DomainStatus.IN_PROGRESS}
    if retry_incomplete:
        wanted.add(DomainStatus.INCOMPLETE)
    statuses = {
        domain: DomainStore(year, domain).status(settings.articles_per_domain_year)
        for domain, _ in domains
    }
    counts = Counter(statuses.values())
    logger.info(
        "%d: %s",
        year,
        ", ".join(f"{status.value}={counts[status]}" for status in DomainStatus),
    )
    if counts[DomainStatus.INCOMPLETE] and not retry_incomplete:
        logger.info(
            "%d: %d incomplete domains skipped (use --retry-incomplete to continue them)",
            year,
            counts[DomainStatus.INCOMPLETE],
        )
    return [
        (domain, stratum) for domain, stratum in domains if statuses[domain] in wanted
    ]


def main() -> None:
    """Fetch articles year by year, each year from the crawl listed for it."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", default=None, help="process only this domain (test)")
    parser.add_argument(
        "--year", type=int, default=None, help="process only this year (test)"
    )
    parser.add_argument(
        "--relaxed", action="store_true", help="do not require article markup"
    )
    parser.add_argument(
        "--retry-incomplete",
        action="store_true",
        help="also continue domains that finished with fewer articles than the quota",
    )
    args = parser.parse_args()

    try:
        crawl_map = settings.crawl_map
    except CrawlMapError as exc:
        raise SystemExit(str(exc)) from exc
    if args.year is not None and args.year not in crawl_map:
        parser.error(f"year {args.year} is not in {settings.crawls_file}")
    years = [args.year] if args.year is not None else list(crawl_map)

    domains = _load_domains(args.only)
    session = build_session()
    for year in years:
        crawl_id = crawl_map[year]
        todo = _select_todo(year, domains, retry_incomplete=args.retry_incomplete)
        logger.info("=== %d <- %s: %d domains to fetch", year, crawl_id, len(todo))
        if not todo:
            continue
        candidates = find_candidates(
            session, [domain for domain, _ in todo], crawl_id=crawl_id
        )
        with tqdm(todo, desc=f"{year} domains", unit="dom", position=0) as domain_bar:
            for domain, stratum in domain_bar:
                domain_bar.set_postfix_str(domain)
                run_domain(
                    session,
                    domain=domain,
                    stratum=stratum,
                    year=year,
                    crawl_id=crawl_id,
                    candidates=candidates[domain],
                    relaxed=args.relaxed,
                )
    rebuild_meta()


if __name__ == "__main__":
    main()
